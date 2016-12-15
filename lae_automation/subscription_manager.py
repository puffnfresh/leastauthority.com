"""
This module implement an HTTP-accessible microservice which
provides persistence of S4 subscriptions.
"""

from json import dumps

import attr
from attr import validators

from twisted.web.resource import Resource
from twisted.web.http import CREATED, NO_CONTENT
from twisted.web.server import Site
from twisted.python.usage import Options as _Options, UsageError
from twisted.python.filepath import FilePath
from twisted.application.internet import StreamServerEndpointService
from twisted.internet.endpoints import serverFromString

from lae_util import validators as my_validators
from lae_util.fileutil import make_dirs

class Subscriptions(Resource):
    """
    GET / -> list of subscription identifiers
    PUT /<subscription id> -> create new subscription
    DELETE /<subscription id> -> cancel an existing subscription
    """
    def __init__(self, database):
        Resource.__init__(self)
        self.database = database
        
    def getChild(self, name, request):
        return Subscription(self.database, name)

    def render_GET(self, request):
        subscriptions = self.database.list_subscriptions_identifiers()
        request.responseHeaders.setRawHeaders(u"content-type", [u"application/json"])
        return dumps(dict(subscriptions=subscriptions))


class Subscription(Resource):
    def __init__(self, database, subscription_id):
        self.database = database
        self.subscription_id = subscription_id

    def render_PUT(self, request):
        payload = loads(request.content.read())
        self.database.create_subscription(subscription_id=self.subscription_id, **payload)
        request.setResponseCode(CREATED)
        return b""

    def render_DELETE(self, request):
        self.database.deactivate_subscription(subscription_id=self.subscription_id)
        request.setResponseCode(NO_CONTENT)
        return b""


# XXX Just filesystem based for now (easier to get right quickly;
# dunno what database makes sense yet, etc).  At some point, put a
# real database here.
@attr.s(frozen=True)
class SubscriptionDatabase(object):
    path = attr.ib(validator=my_validators.all(
        validators.instance_of(FilePath),
        my_validators.after(
            lambda i, a, v: v.basename(),
            validators.instance_of(unicode),
        ),
    ))

    @classmethod
    def from_directory(cls, path):
        if not path.exists():
            raise ValueError("State directory ({}) does not exist.".format(path.path))
        if not path.isdir():
            raise ValueError("State path ({}) is not a directory.".format(path.path))
        return SubscriptionDatabase(path=path)

    def _subscription_path(self, subscription_id):
        return self.path.child(subscription_id + u".json")

    def _subscription_state(self, subscription_id, introducer_furl, bucket_name):
        return dict(
            version=1,
            details=dict(
                active=True,
                subscription_id=subscription_id,
                introducer_furl=introducer_furl,
                bucket_name=bucket_name,
            ),
        )

    def _write(self, path, content):
        flags = (
            # Create the subscription file
            O_CREAT
            # Fail if it already exists
            | O_EXCL
            # Open it for writing only
            | O_WRONLY
        )
        with open(path.path, flags) as subscription_file:
            # XXX Crash here and we have inconsistent state on disk.
            # It would be better to write to a temporary file and then
            # renameat2(..., RENAME_NOREPLACE) but Python doesn't
            # expose that API.
            #
            # At least we can dump the whole config in memory and then
            # write it in one go.
            subscription_file.write(dumps(state))

    def create_subscription(self, subscription_id, introducer_furl, bucket_name):
        path = self._subscription_path(subscription_id)
        state = self._subscription_state(subscription_id, introducer_furl, bucket_name)
        self._write(path, dumps(state))

    def list_subscriptions_identifiers(self):
        return [
            child.basename()[:len(u".json")]
            for child in self.path.children()
        ]


def required(options, key):
    if options[key] is None:
        raise UsageError("--{} is required.".format(key))


def make_resource(path):
    v1 = Resource()
    v1.putChild("subscriptions", Subscriptions(SubscriptionDatabase.from_directory(path)))
    
    root = Resource()
    root.putChild("v1", v1)

    return root


class Options(_Options):
    optParameters = [
        ("state-path", "p", None, "Path to the subscription state directory."),
        ("listen-address", "l", None, "Endpoint on which the server should listen."),
    ]

    def postOptions(self):
        required(self, "state-path")
        required(self, "listen-address")
        self["state-path"] = FilePath(self["state-path"].decode("utf-8"))

def makeService(options):
    from twisted.internet import reactor

    make_dirs(options["state-path"].path)
    site = Site(make_resource(options["state-path"]))

    return StreamServerEndpointService(
        serverFromString(reactor, options["listen-address"]),
        site,
    )