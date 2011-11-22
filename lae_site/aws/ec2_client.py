
from txaws.ec2.client import EC2Client

from lae_site.aws.queryapi import xml_parse, xml_find


class SoupedUpEC2Client(EC2Client):
    def allocate_address(self):
        """
        Reference: http://docs.amazonwebservices.com/AWSEC2/latest/APIReference/index.html?ApiReference-query-AllocateAddress.html
        """
        query = self.query_factory(
            action="AllocateAddress", creds=self.creds, endpoint=self.endpoint,
            other_params={})
        d = query.submit()
        d.addCallback(AllocateAddressResponse.parse)
        return d

    def associate_address(self, instance_id, ip_address):
        """
        Reference: http://docs.amazonwebservices.com/AWSEC2/latest/APIReference/index.html?ApiReference-query-AssociateAddress.html
        """
        query = self.query_factory(
            action="AssociateAddress", creds=self.creds, endpoint=self.endpoint,
            other_params={'InstanceId': instance_id, 'PublicIp': ip_address})
        d = query.submit()
        d.addCallback(AssociateAddressResponse.parse)
        return d

    def getpubip(self):
        """Describe current instances."""
        query = self.query_factory(
            action="DescribeInstances", creds=self.creds,
            endpoint=self.endpoint, other_params={})
        #print "query: %s"%query
        d = query.submit()
        d.addCallback(GetPubIPResponse.parse)
        return d

class GetPubIPResponse:
    @classmethod
    def parse(cls, body):
        doc = xml_parse(body)
        print "Finished call to xml_parse."
        print doc
        dnsName = xml_find(doc, u'dnsName')[0].text.strip()
        prefix_plus_public_ip = dnsName[:dnsName.find('.')]
        public_ip_without_prefix = prefix_plus_public_ip[prefix_plus_public_ip.find('-')+1:]
        public_ip = public_ip_without_prefix.replace('-','.')
        return public_ip

class AllocateAddressResponse:
    @classmethod
    def parse(cls, body):
        doc = xml_parse(body)
        print "Finished call to xml_parse."
        print doc
        public_ip = xml_find(doc, u'publicIp').text.strip()
        return public_ip


class AssociateAddressResponse:
    @classmethod
    def parse(cls, body):
        doc = xml_parse(body)
        ret = xml_find(doc, u'return').text.strip()
        return ret == "true"
