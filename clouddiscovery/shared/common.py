import datetime
import re
from typing import NamedTuple, List, Optional, Dict

import boto3

VPCE_REGEX = re.compile(r'(?<=sourcevpce")(\s*:\s*")(vpce-[a-zA-Z0-9]+)', re.DOTALL)
SOURCE_IP_ADDRESS_REGEX = re.compile(
    r'(?<=sourceip")(\s*:\s*")([a-fA-F0-9.:/%]+)', re.DOTALL
)


class bcolors:
    colors = {
        "HEADER": "\033[95m",
        "OKBLUE": "\033[94m",
        "OKGREEN": "\033[92m",
        "WARNING": "\033[93m",
        "FAIL": "\033[91m",
        "ENDC": "\033[0m",
        "BOLD": "\033[1m",
        "UNDERLINE": "\033[4m",
    }


class BaseAwsOptions(NamedTuple):
    session: boto3.Session
    region_name: str

    def client(self, service_name: str):
        return self.session.client(service_name, region_name=self.region_name)

    def resulting_file_name(self, suffix):
        return "{}_{}_{}".format(self.account_number(), self.region_name, suffix)

    def account_number(self):
        client = self.session.client("sts", region_name=self.region_name)
        account_id = client.get_caller_identity()["Account"]
        return account_id


class ResourceDigest(NamedTuple):
    id: str
    type: str


class ResourceEdge(NamedTuple):
    from_node: ResourceDigest
    to_node: ResourceDigest
    label: str = None


class ResourceTag(NamedTuple):
    key: str
    value: str


class Resource(NamedTuple):
    digest: ResourceDigest
    name: str
    details: str = ""
    group: str = ""
    tags: List[ResourceTag] = []


def resource_tags_from_tuples(tuples: List[Dict[str, str]]) -> List[ResourceTag]:
    """
        List of key-value tuples that store tags, syntax:
        [
            {
                'Key': 'string',
                'Value': 'string'
            },
        ]
    """
    result = []
    for tuple_elem in tuples:
        result.append(ResourceTag(key=tuple_elem["Key"], value=tuple_elem["Value"]))
    return result


def resource_tags_from_dict(tags: Dict[str, str]) -> List[ResourceTag]:
    """
        List of key-value dict that store tags, syntax:
        {
            'string': 'string'
        }
    """
    result = []
    for key, value in tags.items():
        result.append(ResourceTag(key=key, value=value))
    return result


class ResourceProvider:
    def __init__(self):
        """
        Base provider class that provides resources and relationships.

        The class should be implemented to return resources of the same type
        """
        self.relations_found: List[ResourceEdge] = []

    def get_resources(self) -> List[Resource]:
        return []

    def get_relations(self) -> List[ResourceEdge]:
        return self.relations_found


def get_name_tag(d) -> Optional[str]:
    return get_tag(d, "Name")


def get_tag(d, tag_name) -> Optional[str]:
    for k, v in d.items():
        if k == "Tags":
            for value in v:
                if value["Key"] == tag_name:
                    return value["Value"]

    return None


def generate_session(profile_name):
    try:
        return boto3.Session(profile_name=profile_name)
    # pylint: disable=broad-except
    except Exception as e:
        message = "You must configure awscli before use this script.\nError: {0}".format(
            str(e)
        )
        exit_critical(message)


def exit_critical(message):
    log_critical(message)
    raise SystemExit


def log_critical(message):
    print(bcolors.colors.get("FAIL"), message, bcolors.colors.get("ENDC"), sep="")


def message_handler(message, position):
    print(bcolors.colors.get(position), message, bcolors.colors.get("ENDC"), sep="")


# pylint: disable=inconsistent-return-statements
def datetime_to_string(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()
