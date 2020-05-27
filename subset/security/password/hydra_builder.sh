#!/bin/bash

# A quick script to retrieve the parameters required for a hydra command, by parsing the webpage.
# HTTP_Form this will be an experimental feature for now, to build the basis for others to improve.

# Process:
# Read the html of a given login webpage.
# - Use grep to look for:
#   - Only trigger this test if an html file is retrieved by sending a get request to the http port.
#   - The form action, method, username field, password field and button field.
#   - Run checks to make sure fields can be found in webpage.
#   - To aid with this, a predetermined set of likely names are used to find these fields.
# - Once these are found, use it to build the hydra command.

function get_webpage_html() {
  echo "$(curl -X GET $1)"
}

function clean_up_field() {
  echo "$1" | tr -d '"' | tr -d " " | sed -E "s/${2}//g" | tr -d ">"
}

function get_action_field() {
  action_field="$(echo "$1" | tr -d "\\" | grep -oE ".*<form.*action=\".*\".*" | grep -oE "action=.*\s")"
  clean_up_field $action_field "action="
}

function get_method_field() {
  method_field="$(echo "$1" | tr -d "\\" | grep -oE ".*<form.*method=\".*\".*" | grep -oE "method=.*>")"
  clean_up_field $method_field "method="
}

function get_username_field() {
  username_field="$(echo "$1" | tr -d "\\" | grep -oE ".*<input.*type=.*text.*.*name=.*>" | grep -oE "name=\".*\"")"
  clean_up_field $username_field "name="
}

function get_password_field() {
  password_field="$(echo "$1" | tr -d "\\" | grep -oE ".*<input.*type=.*password.*.*name=.*>" | grep -oE "name=\".*\"")"
  clean_up_field $password_field "name="
}

function get_login_field() {
  login_field="$(echo "$1" | tr -d "\\" | grep -oE ".*<input.*type=.*submit.*.*name=.*>" | grep -oE "name=\".*\"")"
  clean_up_field $login_field "name="
}

# $1 localhost
# $2 port
# $3 page
function get_hydra_form_command2() {
  action_field="$(get_action_field "$(cat $3)")"
  method_field="$(get_method_field "$(cat $3)")"
  username="$(get_username_field "$(cat $3)")"
  password="$(get_password_field "$(cat $3)")"
  login="$(get_login_field "$(cat $3)")"
  echo "hydra $1 -s $2 -V -L resources/usernames.txt -P resources/passwords.txt http-$method_field \"/$action_field:$username=^USER^&$password=^PASS^&$login_field=Login:S=Welcome\""
}

get_hydra_form_command2 127.0.0.1 80 resources/test.html
