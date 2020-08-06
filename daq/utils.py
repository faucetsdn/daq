"""Utility functions for DAQ"""

from google.protobuf import json_format
import yaml


def yaml_proto(file_name, proto_func):
    """Load a yaml file into a proto object"""
    with open(file_name) as stream:
        file_dict = yaml.safe_load(stream)
    return json_format.ParseDict(file_dict, proto_func())


def proto_dict(message,
               including_default_value_fields=False,
               preserving_proto_field_name=True):
    """Convert a proto message to a standard dict object"""
    return json_format.MessageToDict(
        message,
        including_default_value_fields=including_default_value_fields,
        preserving_proto_field_name=preserving_proto_field_name
    )


def proto_json(message):
    """Convert a proto message to a json string"""
    return json_format.MessageToJson(
        message,
        including_default_value_fields=True,
        preserving_proto_field_name=True,
    )


def dict_proto(message, proto_func, ignore_unknown_fields=False):
    """Convert a standard dict object to a proto object"""
    return json_format.ParseDict(message, proto_func(), ignore_unknown_fields)
