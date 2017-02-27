
from io import BytesIO
from base64 import b32encode
from json import dumps

import attr

from hypothesis import given, assume

from testtools.matchers import Equals, AfterPreprocessing

from twisted.internet.defer import succeed
from twisted.python.filepath import FilePath
from twisted.python.url import URL

from foolscap.furl import decode_furl

from lae_util.testtools import TestCase
from lae_util.fileutil import make_dirs
from lae_automation import model, signup
from lae_automation.signup import activate_ex

from lae_automation.subscription_manager import broken_client
from lae_automation.test.strategies import (
    port_numbers, emails, old_secrets, deployment_configuration, subscription_details,
    customer_id, subscription_id,
)

# Vector data for request responses: activate desktop-, verify-, and describeEC2- responses.
ACCESSKEYID = 'TEST'+'A'*16
SECRETACCESSKEY = 'TEST'+'A'*36
REQUESTID = 'TEST'+'A'*32

# Test vector request and response to the make http request: describe instances

# DescribeInstances
describeEC2instresponse = """<?xml version="1.0" encoding="UTF-8"?>
<DescribeInstancesResponse xmlns="http://ec2.amazonaws.com/doc/2008-12-01/">
  <requestId>TEST</requestId>
  <reservationSet>
    <item>
      <reservationId>TEST</reservationId>
      <ownerId>TEST</ownerId>
      <groupSet><item><groupId>CustomerDefault</groupId></item></groupSet>
      <instancesSet>
        <item>
          <instanceId>TEST</instanceId>
          <imageId>TEST</imageId>
          <instanceState><code>TEST</code><name>TEST</name></instanceState>
          <privateDnsName>TESTinternal</privateDnsName>
          <dnsName>ec2-50-17-175-164.compute-1.amazonaws.com</dnsName>
          <reason/>
          <keyName>TEST</keyName>
          <amiLaunchIndex>0</amiLaunchIndex>
          <productCodes/>
          <instanceType>t1.TEST</instanceType>
          <launchTime>TEST</launchTime>
          <placement><availabilityZone>TEST</availabilityZone></placement>
          <kernelId>TEST</kernelId>
        </item>
      </instancesSet>
    </item>
  </reservationSet>
</DescribeInstancesResponse>"""

# CreateTags
createtagsresponse = """<CreateTagsResponse xmlns="http://ec2.amazonaws.com/doc/2011-11-01/">
  <requestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</requestId>
  <return>true</return>
</CreateTagsResponse>"""

# Get Console
getconsoleoutputresponse = """<GetConsoleOutputResponse xmlns="http://ec2.amazonaws.com/doc/2013-02-01/">
  <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
  <instanceId>i-MOCKTEST</instanceId>
  <timestamp>2010-10-14T01:12:41.000Z</timestamp>
  <output>MjAxMy0wNC0xMSAyMDozMjoyMiwxMTYgLSBfX2luaXRfXy5weVtXQVJOSU5HXTogVW5oYW5kbGVk\nIG5vbi1tdWx0aXBhcnQgdXNlcmRhdGEgJycNCkdlbmVyYXRpbmcgcHVibGljL3ByaXZhdGUgcnNh\nIGtleSBwYWlyLg0KWW91ciBpZGVudGlmaWNhdGlvbiBoYXMgYmVlbiBzYXZlZCBpbiAvZXRjL3Nz\naC9zc2hfaG9zdF9yc2Ffa2V5Lg0KWW91ciBwdWJsaWMga2V5IGhhcyBiZWVuIHNhdmVkIGluIC9l\ndGMvc3NoL3NzaF9ob3N0X3JzYV9rZXkucHViLg0KVGhlIGtleSBmaW5nZXJwcmludCBpczoNCmI4\nOjgzOmNmOjFkOjk3OjRiOjQ0OjhmOmE3OjA1OjI5OjRlOmY2OjFlOmFmOmRkIHJvb3RAaXAtMTAt\nMTk0LTI5LTM5DQpUaGUga2V5J3MgcmFuZG9tYXJ0IGltYWdlIGlzOg0KKy0tWyBSU0EgMjA0OF0t\nLS0tKw0KfCAgICAgICAgICAgICAgICAgfA0KfCAgICAgICAgICAgLiAgICAgfA0KfCAgICAgICAg\nKyArICAgICAgfA0KfCAgICAgICA9ICsgKyAgICAgfA0KfCAgICAgIC4gUyA9ICsgICAgfA0KfCAg\nICAgLiAuIG8gQiAgICAgfA0KfCAgICAuIG8gLiAqIC4gICAgfA0KfCAgICAgbyBvICsgKyAuICAg\nfA0KfCAgICAgIG8gLiBvIC4gRSAgfA0KKy0tLS0tLS0tLS0tLS0tLS0tKw0KR2VuZXJhdGluZyBw\ndWJsaWMvcHJpdmF0ZSBkc2Ega2V5IHBhaXIuDQpZb3VyIGlkZW50aWZpY2F0aW9uIGhhcyBiZWVu\nIHNhdmVkIGluIC9ldGMvc3NoL3NzaF9ob3N0X2RzYV9rZXkuDQpZb3VyIHB1YmxpYyBrZXkgaGFz\nIGJlZW4gc2F2ZWQgaW4gL2V0Yy9zc2gvc3NoX2hvc3RfZHNhX2tleS5wdWIuDQpUaGUga2V5IGZp\nbmdlcnByaW50IGlzOg0KMjU6ZmQ6Nzk6MjE6MmM6NjI6ZDI6MGQ6NzI6MGE6NGM6NTg6MGI6NmE6\nNWM6MjAgcm9vdEBpcC0xMC0xOTQtMjktMzkNClRoZSBrZXkncyByYW5kb21hcnQgaW1hZ2UgaXM6\nDQorLS1bIERTQSAxMDI0XS0tLS0rDQp8RS5vKisgLiBvICAgICAgICB8DQp8by5vLi5vID0gKyAu\nICAgICB8DQp8Lm8gIC4gbyA9ID0gbyAuICB8DQp8LiAgICAgIG8gKyBvIG8gLiB8DQp8ICAgICAg\nICBTICAgbyAuICB8DQp8ICAgICAgICAgICAgIC4gICB8DQp8ICAgICAgICAgICAgICAgICB8DQp8\nICAgICAgICAgICAgICAgICB8DQp8ICAgICAgICAgICAgICAgICB8DQorLS0tLS0tLS0tLS0tLS0t\nLS0rDQpHZW5lcmF0aW5nIHB1YmxpYy9wcml2YXRlIGVjZHNhIGtleSBwYWlyLg0KWW91ciBpZGVu\ndGlmaWNhdGlvbiBoYXMgYmVlbiBzYXZlZCBpbiAvZXRjL3NzaC9zc2hfaG9zdF9lY2RzYV9rZXku\nDQpZb3VyIHB1YmxpYyBrZXkgaGFzIGJlZW4gc2F2ZWQgaW4gL2V0Yy9zc2gvc3NoX2hvc3RfZWNk\nc2Ffa2V5LnB1Yi4NClRoZSBrZXkgZmluZ2VycHJpbnQgaXM6DQo0MjpjOTowZTpiNTozMzo3NDo1\nZDowMDpkODo1ODowZTo1MDozMjpiNTpiNDoyNiByb290QGlwLTEwLTE5NC0yOS0zOQ0KVGhlIGtl\neSdzIHJhbmRvbWFydCBpbWFnZSBpczoNCistLVtFQ0RTQSAgMjU2XS0tLSsNCnwgICAgKytCPStv\nLm8uICAgIHwNCnwgICAgIEJvTy4gLiAgICAgIHwNCnwgICAgRSBAIC4gICAgICAgIHwNCnwgICAg\nICogbyAgICAgICAgIHwNCnwgICAgICBvIFMgICAgICAgIHwNCnwgICAgICAgLiAgICAgICAgIHwN\nCnwgICAgICAgICAgICAgICAgIHwNCnwgICAgICAgICAgICAgICAgIHwNCnwgICAgICAgICAgICAg\nICAgIHwNCistLS0tLS0tLS0tLS0tLS0tLSsNClNraXBwaW5nIHByb2ZpbGUgaW4gL2V0Yy9hcHBh\ncm1vci5kL2Rpc2FibGU6IHVzci5zYmluLnJzeXNsb2dkDQogKiBTdGFydGluZyBBcHBBcm1vciBw\ncm9maWxlcyAgICAgICAbWzgwRyANG1s3NEdbIE9LIF0NCmxhbmRzY2FwZS1jbGllbnQgaXMgbm90\nIGNvbmZpZ3VyZWQsIHBsZWFzZSBydW4gbGFuZHNjYXBlLWNvbmZpZy4NCkdlbmVyYXRpbmcgbG9j\nYWxlcy4uLgogIGVuX1VTLlVURi04Li4uIGRvbmUKR2VuZXJhdGlvbiBjb21wbGV0ZS4KZWMyOiAK\nZWMyOiAjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMj\nIyMjIyMjIyMjCmVjMjogLS0tLS1CRUdJTiBTU0ggSE9TVCBLRVkgRklOR0VSUFJJTlRTLS0tLS0K\nZWMyOiAxMDI0IDI1OmZkOjc5OjIxOjJjOjYyOmQyOjBkOjcyOjBhOjRjOjU4OjBiOjZhOjVjOjIw\nICByb290QGlwLTEwLTE5NC0yOS0zOSAoRFNBKQplYzI6IDI1NiA0MjpjOTowZTpiNTozMzo3NDo1\nZDowMDpkODo1ODowZTo1MDozMjpiNTpiNDoyNiAgcm9vdEBpcC0xMC0xOTQtMjktMzkgKEVDRFNB\nKQplYzI6IDIwNDggYjg6ODM6Y2Y6MWQ6OTc6NGI6NDQ6OGY6YTc6MDU6Mjk6NGU6ZjY6MWU6YWY6\nZGQgIHJvb3RAaXAtMTAtMTk0LTI5LTM5IChSU0EpCmVjMjogLS0tLS1FTkQgU1NIIEhPU1QgS0VZ\nIEZJTkdFUlBSSU5UUy0tLS0tCmVjMjogIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMj\nIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIwotLS0tLUJFR0lOIFNTSCBIT1NUIEtFWSBLRVlT\nLS0tLS0KZWNkc2Etc2hhMi1uaXN0cDI1NiBBQUFBRTJWalpITmhMWE5vWVRJdGJtbHpkSEF5TlRZ\nQUFBQUlibWx6ZEhBeU5UWUFBQUJCQkd6d1l6WjF1eXVDSHJNR3ZHZHQyazFKakRhUTl1R2RGQXM2\nQ3k3dlkyTW95c3IxbmZaVE1KME5BV2I4MlkxZ3I0amZqbUIwY1BtQks4VGcxd2Urb1BvPSByb290\nQGlwLTEwLTE5NC0yOS0zOQpzc2gtcnNhIEFBQUFCM056YUMxeWMyRUFBQUFEQVFBQkFBQUJBUUNn\nb0M4OXZlNjFVaS9VaTVwbklTdmlkWVcvdVVyVFN6MEYwajBjenV6RHlTUGwvUnF4S3VadllRQWp1\nZzZPRW4wT2htbmg0Mmo2RGs0THIwOUg5R0xKVHVEdjJrVE5oUUY5ODBSWFVQcTNOVHlvengxc3A4\nMjRYM3pHK2VQaWlZejJPUUkvQ2YzcjJjQVVxZ2dKakE4d1BhV1NYeXV5cC9MczI4NjFYdnNuUzVp\nSVNueWxwRXVOL09YTkZSbXVKUnpzK2hjazV1ck1Weno1QWRibjl6U0svTkpSUFlTM3FTZnZDTjZw\nWEJ5TGNFSlVFTkNLSUE4MFZSSEtudi9pc0tzY0Fadm1ESkNvclJXWFJ2eEI2eExCMlZuVGJxQlVU\nUWErMHpyemZRU0pEOEMyMlliUGxnd3NGdG4wNzl3T2trYVF0ZC9BaGhQWGZUbEFVbGpBZkMvQiBy\nb290QGlwLTEwLTE5NC0yOS0zOQotLS0tLUVORCBTU0ggSE9TVCBLRVkgS0VZUy0tLS0tCmNsb3Vk\nLWluaXQgYm9vdCBmaW5pc2hlZCBhdCBUaHUsIDExIEFwciAyMDEzIDIwOjMyOjMyICswMDAwLiBV\ncCAyOC4yNCBzZWNvbmRzCg==\n</output>
</GetConsoleOutputResponse>"""

MOCKSERVERSSHFP = 'b8:83:cf:1d:97:4b:44:8f:a7:05:29:4e:f6:1e:af:dd'
MOCKHASHEDPUBKEY = """|1|lrzohCU8y8Obch3wa7+gnvEJuI0=|I1GQU+vw3MgMnyvY+SxnhCyArHg= ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCgoC89ve61Ui/Ui5pnISvidYW/uUrTSz0F0j0czuzDySPl/RqxKuZvYQAjug6OEn0Ohmnh42j6Dk4Lr09H9GLJTuDv2kTNhQF980RXUPq3NTyozx1sp824X3zG+ePiiYz2OQI/Cf3r2cAUqggJjA8wPaWSXyuyp/Ls2861XvsnS5iISnylpEuN/OXNFRmuJRzs+hck5urMVzz5Adbn9zSK/NJRPYS3qSfvCN6pXByLcEJUENCKIA80VRHKnv/isKscAZvmDJCorRWXRvxB6xLB2VnTbqBUTQa+0zrzfQSJD8C22YbPlgwsFtn079wOkkaQtd/AhhPXfTlAUljAfC/B"""

# Vector data for the config file data:
from lae_automation.test.test_vectors import MOCKJSONCONFIGFILE
CONFIGFILEJSON = MOCKJSONCONFIGFILE

ZEROPRODUCT = {
  "products": [],
  "ec2_access_key_id":    "TESTEC2EC2EC2EC2EC2E",
  "ec2_secret_path":      "mock_ec2_secret",
  "s3_access_key_id":     u"TESTS3S3S3S3S3S3S3S3",
  "s3_secret_path":       "mock_s3_secret",
  "admin_keypair_name":   "ADMINKEYS",
  "admin_privkey_path":   "ADMINKEYS.pem",
  "monitor_pubkey_path":  "MONITORKEYS.pub",
  "monitor_privkey_path": "MONITORKEYS.pem"
}

MOCKEC2SECRETCONTENTS = 'EC2'*13+'E'
MOCKS3SECRETCONTENTS = u'S3' * 20
MONITORPUBKEY = 'MONITOR PUBLIC KEY'


class TestSignupModule(TestCase):
    def setUp(self):
        super(TestSignupModule, self).setUp()
        self.mockconfigdir = FilePath('./test_signup').child('TestSignupModule')
        make_dirs(self.mockconfigdir.path)
        self.SIGNUPSPATH = 'mock_signups.csv'
        self.CONFIGFILEPATH = 'init_test_config.json'
        self.SERVERINFOPATH = 'mock_serverinfo.csv'
        self.EC2SECRETPATH = 'mock_ec2_secret'
        self.S3SECRETPATH = 'mock_s3_secret'
        self.MONITORPUBKEYPATH = 'MONITORKEYS.pub'

        self.MEMAIL = 'MEMAIL'
        self.MKEYINFO = 'MKEYINFO'
        self.MCUSTOMER_ID = u'cus_x14Charactersx'
        self.MSUBSCRIPTION_ID = u'sub_x14Characterx'
        self.MPLAN_ID = 'XX_consumer_iteration_#_GREEKLETTER#_2XXX-XX-XX'
        self.MSECRETSFILE = 'MSECRETSFILE'
        self.MENCODED_IDS = 'on2wex3yge2eg2dbojqwg5dfoj4a-mn2xgx3yge2eg2dbojqwg5dfojzxq'

        FilePath(self.SIGNUPSPATH).setContent('')
        FilePath(self.CONFIGFILEPATH).setContent(CONFIGFILEJSON)
        FilePath(self.SERVERINFOPATH).setContent('')
        FilePath(self.EC2SECRETPATH).setContent(MOCKEC2SECRETCONTENTS)
        FilePath(self.S3SECRETPATH).setContent(MOCKS3SECRETCONTENTS)
        FilePath(self.MONITORPUBKEYPATH).setContent(MONITORPUBKEY)

        self.DEPLOYMENT_CONFIGURATION = model.DeploymentConfiguration(
            domain=u"s4.example.com",
            kubernetes_namespace=u"testing",
            subscription_manager_endpoint=URL.fromText(u"http://localhost/"),
            products=[{"description": "stuff"}],
            s3_access_key_id=ZEROPRODUCT["s3_access_key_id"],
            s3_secret_key=MOCKS3SECRETCONTENTS,

            introducer_image=u"tahoe-introducer",
            storageserver_image=u"tahoe-storageserver",

            ssec2_access_key_id=ZEROPRODUCT["s3_access_key_id"],
            ssec2_secret_path=self.S3SECRETPATH,

            ssec2admin_keypair_name=ZEROPRODUCT["admin_keypair_name"],
            ssec2admin_privkey_path=ZEROPRODUCT["admin_privkey_path"],

            monitor_pubkey_path=ZEROPRODUCT["monitor_pubkey_path"],
            monitor_privkey_path=ZEROPRODUCT["monitor_privkey_path"],

            secretsfile=open(self.MSECRETSFILE, "a+b"),
            serverinfopath=self.SERVERINFOPATH,
        )
        self.SUBSCRIPTION = model.SubscriptionDetails(
            bucketname="lae-" + self.MENCODED_IDS,
            oldsecrets=old_secrets().example(),
            customer_email=self.MEMAIL,
            customer_pgpinfo=self.MKEYINFO,
            product_id=u"filler",
            customer_id=self.MCUSTOMER_ID,
            subscription_id=self.MSUBSCRIPTION_ID,
            introducer_port_number=12345,
            storage_port_number=12346,
        )

    def test_no_products(self):
        invalid = attr.asdict(self.DEPLOYMENT_CONFIGURATION)
        invalid["products"] = []
        self.assertRaises(
            ValueError,
            model.DeploymentConfiguration,
            **invalid
        )

    def test_get_bucket_name(self):
        self.failUnlessEqual(b32encode("abc"), "MFRGG===")
        self.failUnlessEqual(b32encode("def"), "MRSWM===")
        self.failUnlessEqual(signup.get_bucket_name("abc", "def"), "lae-mfrgg-mrswm")


TestSignupModule.test_activate_subscribed_service.__func__.skip = "mostly obsolete"

# New tests for signup.  Trying to keep a healthy distance from old
# test implementation.
class SignupTests(TestCase):
    def test_subscription_manager_not_listening(self):
        """
        If the subscription manager doesn't accept the new subscription,
        ``activate_subscribed_service`` returns a ``Deferred`` that
        fails with the details.
        """
        deploy_config = deployment_configuration().example()
        details = subscription_details().example()
        d = signup.just_activate_subscription(
            deploy_config, details,
            clock=None, smclient=broken_client(),
        )
        self.failureResultOf(d)



class ActivateTests(TestCase):
    @given(
        emails(), customer_id(), subscription_id(), old_secrets(),
        port_numbers(), port_numbers(),
    )
    def test_emailed_introducer_furl(
            self,
            customer_email,
            customer_id,
            subscription_id,
            old_secrets,
            introducer_port_number,
            storage_port_number,
    ):
        """
        The introducer furl included in the activation email points at the server
        and port identified by the activated subscription detail object.
        """
        assume(introducer_port_number != storage_port_number)

        emails = []

        def just_activate_subscription(
                deploy_config, subscription, clock, smclient,
        ):
            return succeed(
                attr.assoc(
                    subscription,
                    introducer_port_number=introducer_port_number,
                    storage_port_number=storage_port_number,
                    oldsecrets=old_secrets,
                ),
            )

        def send_signup_confirmation(
                customer_email, external_introducer_furl, customer_keyinfo, stdout, stderr,
        ):
            emails.append((customer_email, "success", external_introducer_furl))
            return succeed(None)

        def send_notify_failure(
                reason, customer_email, logfilename, stdout, stderr,
        ):
            emails.append((customer_email, "failure", reason))
            return succeed(None)

        root = FilePath(self.mktemp())
        root.makedirs()

        secrets_path = root.child(u"secrets_path")
        secrets_path.makedirs()

        s3_key_path = root.child(u"s3.key")
        s3_key_path.setContent(b"efgh")

        plan_name = u"foo"
        plan_identifier = u"foobar"

        automation_config_path = root.child(u"automation.json")
        automation_config_path.setContent(dumps({
            u"products": [{
                u"amount": 123,
                u"interval": 321,
                u"currency": u"USD",
                u"plan_name": plan_name,
                u"plan_ID": plan_identifier,
                u"plan_trial_period_days": 12,
                u"ami_image_id": u"ami-123",
                u"instance_size": u"medium",
                u"statement_description": u"no comment",
            }],
            u"s3_access_key_id": u"abcd",
            u"s3_secret_path": s3_key_path.path,
        }))

        server_info_path = root.child(u"server-info.csv")

        stdin = BytesIO(dumps([
            customer_email, None, customer_id, plan_identifier, subscription_id,
        ]))
        flapp_stdout_path = root.child(u"flapp.stdout")
        flapp_stderr_path = root.child(u"flapp.stderr")

        d = activate_ex(
            just_activate_subscription,
            send_signup_confirmation,
            send_notify_failure,
            u"s4.example.com",
            URL.fromText(u"http://localhost/"),
            secrets_path,
            automation_config_path,
            server_info_path,
            stdin,
            flapp_stdout_path,
            flapp_stderr_path,
        )
        self.successResultOf(d)

        [(recipient, result, rest)] = emails
        self.expectThat(recipient, Equals(customer_email))
        self.expectThat(result, Equals("success"))

        def get_hint_port(furl):
            tub_id, location_hints, name = decode_furl(furl)
            host, port = location_hints[0].split(u":")
            return int(port)

        self.expectThat(
            rest,
            AfterPreprocessing(
                get_hint_port,
                Equals(introducer_port_number),
            ),
        )
