# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: daq/proto/system_config.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='daq/proto/system_config.proto',
  package='',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=_b('\n\x1d\x64\x61q/proto/system_config.proto\"\xb3\t\n\tDaqConfig\x12\x18\n\x10site_description\x18\x01 \x01(\t\x12\x18\n\x10monitor_scan_sec\x18\x02 \x01(\x05\x12\x1b\n\x13\x64\x65\x66\x61ult_timeout_sec\x18\x03 \x01(\x05\x12\x12\n\nsettle_sec\x18& \x01(\x05\x12\x11\n\tbase_conf\x18\x04 \x01(\t\x12\x11\n\tsite_path\x18\x05 \x01(\t\x12\x1f\n\x17initial_dhcp_lease_time\x18\x06 \x01(\t\x12\x17\n\x0f\x64hcp_lease_time\x18\x07 \x01(\t\x12\x19\n\x11\x64hcp_response_sec\x18\' \x01(\x05\x12\x1e\n\x16long_dhcp_response_sec\x18\x08 \x01(\x05\x12\x10\n\x08\x65xt_ctrl\x18\t \x01(\t\x12\x10\n\x08\x65xt_ofip\x18\n \x01(\t\x12\x10\n\x08\x65xt_ofpt\x18+ \x01(\t\x12\x10\n\x08\x65xt_addr\x18\x0b \x01(\t\x12\x10\n\x08\x65xt_loip\x18\x0c \x01(\t\x12\x10\n\x08\x65xt_dpid\x18) \x01(\t\x12\x10\n\x08\x65xt_intf\x18* \x01(\t\x12\x10\n\x08sec_port\x18\r \x01(\x05\x12\x12\n\nintf_names\x18\x0e \x01(\t\x12\x14\n\x0cstartup_cmds\x18\x0f \x01(\t\x12\x12\n\nhost_tests\x18\x10 \x01(\t\x12\x13\n\x0b\x62uild_tests\x18$ \x01(\x08\x12\x11\n\trun_limit\x18\x11 \x01(\x05\x12\x11\n\tfail_mode\x18\x12 \x01(\x08\x12\x13\n\x0bsingle_shot\x18\" \x01(\x08\x12\x15\n\rresult_linger\x18\x13 \x01(\x08\x12\x0f\n\x07no_test\x18\x14 \x01(\x08\x12\x11\n\tkeep_hold\x18( \x01(\x08\x12\x14\n\x0c\x64\x61q_loglevel\x18\x15 \x01(\t\x12\x18\n\x10mininet_loglevel\x18\x16 \x01(\t\x12\x13\n\x0b\x66inish_hook\x18# \x01(\t\x12\x10\n\x08gcp_cred\x18\x17 \x01(\t\x12\x11\n\tgcp_topic\x18\x18 \x01(\t\x12\x13\n\x0bschema_path\x18\x19 \x01(\t\x12\x11\n\tmud_files\x18\x1a \x01(\t\x12\x14\n\x0c\x64\x65vice_specs\x18\x1b \x01(\t\x12\x13\n\x0btest_config\x18\x1c \x01(\t\x12\x19\n\x11port_debounce_sec\x18\x1d \x01(\x05\x12\x11\n\tfail_hook\x18\x1e \x01(\t\x12\x17\n\x0f\x64\x65vice_template\x18\x1f \x01(\t\x12\x14\n\x0csite_reports\x18  \x01(\t\x12\x1f\n\x17run_data_retention_days\x18! \x01(\x02\x12(\n\x07startup\x18% \x03(\x0b\x32\x17.DaqConfig.StartupEntry\x12\x14\n\x0cswitch_model\x18, \x01(\t\x12\x17\n\x0fswitch_username\x18- \x01(\t\x12\x17\n\x0fswitch_password\x18. \x01(\t\x12/\n\x0b\x66\x61il_module\x18/ \x03(\x0b\x32\x1a.DaqConfig.FailModuleEntry\x1a<\n\x0cStartupEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\x1b\n\x05value\x18\x02 \x01(\x0b\x32\x0c.StartupInfo:\x02\x38\x01\x1a\x31\n\x0f\x46\x61ilModuleEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01\"\x1b\n\x0bStartupInfo\x12\x0c\n\x04opts\x18\x01 \x01(\tb\x06proto3')
)




_DAQCONFIG_STARTUPENTRY = _descriptor.Descriptor(
  name='StartupEntry',
  full_name='DaqConfig.StartupEntry',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='key', full_name='DaqConfig.StartupEntry.key', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='value', full_name='DaqConfig.StartupEntry.value', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=_b('8\001'),
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1126,
  serialized_end=1186,
)

_DAQCONFIG_FAILMODULEENTRY = _descriptor.Descriptor(
  name='FailModuleEntry',
  full_name='DaqConfig.FailModuleEntry',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='key', full_name='DaqConfig.FailModuleEntry.key', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='value', full_name='DaqConfig.FailModuleEntry.value', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=_b('8\001'),
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1188,
  serialized_end=1237,
)

_DAQCONFIG = _descriptor.Descriptor(
  name='DaqConfig',
  full_name='DaqConfig',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='site_description', full_name='DaqConfig.site_description', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='monitor_scan_sec', full_name='DaqConfig.monitor_scan_sec', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='default_timeout_sec', full_name='DaqConfig.default_timeout_sec', index=2,
      number=3, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='settle_sec', full_name='DaqConfig.settle_sec', index=3,
      number=38, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='base_conf', full_name='DaqConfig.base_conf', index=4,
      number=4, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='site_path', full_name='DaqConfig.site_path', index=5,
      number=5, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='initial_dhcp_lease_time', full_name='DaqConfig.initial_dhcp_lease_time', index=6,
      number=6, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='dhcp_lease_time', full_name='DaqConfig.dhcp_lease_time', index=7,
      number=7, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='dhcp_response_sec', full_name='DaqConfig.dhcp_response_sec', index=8,
      number=39, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='long_dhcp_response_sec', full_name='DaqConfig.long_dhcp_response_sec', index=9,
      number=8, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='ext_ctrl', full_name='DaqConfig.ext_ctrl', index=10,
      number=9, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='ext_ofip', full_name='DaqConfig.ext_ofip', index=11,
      number=10, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='ext_ofpt', full_name='DaqConfig.ext_ofpt', index=12,
      number=43, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='ext_addr', full_name='DaqConfig.ext_addr', index=13,
      number=11, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='ext_loip', full_name='DaqConfig.ext_loip', index=14,
      number=12, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='ext_dpid', full_name='DaqConfig.ext_dpid', index=15,
      number=41, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='ext_intf', full_name='DaqConfig.ext_intf', index=16,
      number=42, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='sec_port', full_name='DaqConfig.sec_port', index=17,
      number=13, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='intf_names', full_name='DaqConfig.intf_names', index=18,
      number=14, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='startup_cmds', full_name='DaqConfig.startup_cmds', index=19,
      number=15, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='host_tests', full_name='DaqConfig.host_tests', index=20,
      number=16, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='build_tests', full_name='DaqConfig.build_tests', index=21,
      number=36, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='run_limit', full_name='DaqConfig.run_limit', index=22,
      number=17, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='fail_mode', full_name='DaqConfig.fail_mode', index=23,
      number=18, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='single_shot', full_name='DaqConfig.single_shot', index=24,
      number=34, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='result_linger', full_name='DaqConfig.result_linger', index=25,
      number=19, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='no_test', full_name='DaqConfig.no_test', index=26,
      number=20, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='keep_hold', full_name='DaqConfig.keep_hold', index=27,
      number=40, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='daq_loglevel', full_name='DaqConfig.daq_loglevel', index=28,
      number=21, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='mininet_loglevel', full_name='DaqConfig.mininet_loglevel', index=29,
      number=22, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='finish_hook', full_name='DaqConfig.finish_hook', index=30,
      number=35, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='gcp_cred', full_name='DaqConfig.gcp_cred', index=31,
      number=23, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='gcp_topic', full_name='DaqConfig.gcp_topic', index=32,
      number=24, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='schema_path', full_name='DaqConfig.schema_path', index=33,
      number=25, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='mud_files', full_name='DaqConfig.mud_files', index=34,
      number=26, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='device_specs', full_name='DaqConfig.device_specs', index=35,
      number=27, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='test_config', full_name='DaqConfig.test_config', index=36,
      number=28, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='port_debounce_sec', full_name='DaqConfig.port_debounce_sec', index=37,
      number=29, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='fail_hook', full_name='DaqConfig.fail_hook', index=38,
      number=30, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='device_template', full_name='DaqConfig.device_template', index=39,
      number=31, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='site_reports', full_name='DaqConfig.site_reports', index=40,
      number=32, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='run_data_retention_days', full_name='DaqConfig.run_data_retention_days', index=41,
      number=33, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='startup', full_name='DaqConfig.startup', index=42,
      number=37, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='switch_model', full_name='DaqConfig.switch_model', index=43,
      number=44, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='switch_username', full_name='DaqConfig.switch_username', index=44,
      number=45, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='switch_password', full_name='DaqConfig.switch_password', index=45,
      number=46, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='fail_module', full_name='DaqConfig.fail_module', index=46,
      number=47, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[_DAQCONFIG_STARTUPENTRY, _DAQCONFIG_FAILMODULEENTRY, ],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=34,
  serialized_end=1237,
)


_STARTUPINFO = _descriptor.Descriptor(
  name='StartupInfo',
  full_name='StartupInfo',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='opts', full_name='StartupInfo.opts', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1239,
  serialized_end=1266,
)

_DAQCONFIG_STARTUPENTRY.fields_by_name['value'].message_type = _STARTUPINFO
_DAQCONFIG_STARTUPENTRY.containing_type = _DAQCONFIG
_DAQCONFIG_FAILMODULEENTRY.containing_type = _DAQCONFIG
_DAQCONFIG.fields_by_name['startup'].message_type = _DAQCONFIG_STARTUPENTRY
_DAQCONFIG.fields_by_name['fail_module'].message_type = _DAQCONFIG_FAILMODULEENTRY
DESCRIPTOR.message_types_by_name['DaqConfig'] = _DAQCONFIG
DESCRIPTOR.message_types_by_name['StartupInfo'] = _STARTUPINFO
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

DaqConfig = _reflection.GeneratedProtocolMessageType('DaqConfig', (_message.Message,), dict(

  StartupEntry = _reflection.GeneratedProtocolMessageType('StartupEntry', (_message.Message,), dict(
    DESCRIPTOR = _DAQCONFIG_STARTUPENTRY,
    __module__ = 'daq.proto.system_config_pb2'
    # @@protoc_insertion_point(class_scope:DaqConfig.StartupEntry)
    ))
  ,

  FailModuleEntry = _reflection.GeneratedProtocolMessageType('FailModuleEntry', (_message.Message,), dict(
    DESCRIPTOR = _DAQCONFIG_FAILMODULEENTRY,
    __module__ = 'daq.proto.system_config_pb2'
    # @@protoc_insertion_point(class_scope:DaqConfig.FailModuleEntry)
    ))
  ,
  DESCRIPTOR = _DAQCONFIG,
  __module__ = 'daq.proto.system_config_pb2'
  # @@protoc_insertion_point(class_scope:DaqConfig)
  ))
_sym_db.RegisterMessage(DaqConfig)
_sym_db.RegisterMessage(DaqConfig.StartupEntry)
_sym_db.RegisterMessage(DaqConfig.FailModuleEntry)

StartupInfo = _reflection.GeneratedProtocolMessageType('StartupInfo', (_message.Message,), dict(
  DESCRIPTOR = _STARTUPINFO,
  __module__ = 'daq.proto.system_config_pb2'
  # @@protoc_insertion_point(class_scope:StartupInfo)
  ))
_sym_db.RegisterMessage(StartupInfo)


_DAQCONFIG_STARTUPENTRY._options = None
_DAQCONFIG_FAILMODULEENTRY._options = None
# @@protoc_insertion_point(module_scope)
