#!/usr/bin/env python

############################################################################
# Copyright [2012] [Mathew Branyon (mat.branyon@gmail.com)]
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
############################################################################

from libclient import *

import urllib
import ipaddr
import json


#################
# Show me first #
#################
def index(req, time=0, output='html'):
    mainConfig = getMainConfig()
    appConfig = getAppConfig()

# get username from auth
    user = get_user_name(req)
    message = ""
    admin = http_get("/admin/{0}" . format(user))

# Process form data if we have it
    if req.form:
        ip = ''
        if 'ip' in req.form:
            # this module is supposed to have ip_address (to support ipv4 and ipv6)
            # it doesn't
            # this code currently only supports ipv4
            try:
                ipaddr.IPv4Address(req.form['ip'])
                ip = req.form['ip']
            except ipaddr.AddressValueError:
                ip = get_client_ip(req)
        else:
            ip = get_client_ip(req)

        comment = ""
        if not req.form['comment']:
            comment = None
        else:
            comment = urllib.quote_plus(req.form['comment'])

        message = str(http_get("/create/{0}/{1}/{2}/{3}/{4}" . format(req.form['app'], user, ip, get_client_ip(req), comment)))

# proceed with rendering the page
    ip = get_client_ip(req)

    if user == mainConfig['monitorUser']:
        req.content_type = 'text/plain'

        req.write("{0}\nconnections={1}\n" . format(str(http_get("/create/{0}/{1}/{2}/{3}/{4}" . format(req.form['app'], user, ip, get_client_ip(req), None))), connections_since(time)))
        connection.close()

    else:
        if output == 'html':
            req.content_type = 'text/html'
            req.write(get_html_header())

# create form
            req.write("""
        <h3>{0}</h3>
        <h4>Welcome {1}: Enable service for your current IP Address</h4>
        <form method="POST">
            <table style="border:0">
                <tr style="border:0">
                    <td style="border:0">ip:</td>""" . format(message, user))

            if admin:
                req.write("""
                    <td style="border:0"><input type="text" name="ip" value={0}></td>""" . format(ip))
            else:
                req.write("""
                    <td style="border:0"><input type="hidden" name="ip" value={0}>{0}</td>""" . format(ip))

            req.write("""
                </tr>
                <tr style="border:0">
                    <td style="border:0">comment:</td>
                    <td style="border:0"><input type="text" name="comment"></td>
                </tr>
            </table>""")

            for app in appConfig:
                req.write("""
        <input type="submit" name="app" value="{0}">""" . format(app))

            req.write("""
      </form>
        <br><br>
""")

# if admin, show active connections
            if admin:
                req.write('''
        <table>
            <caption>Active Connections</caption>''')

                req.write('''
            <tr>
            <th>User</th>
                <th>App</th>
                <th>IP</th>
                <th>Timestamp</th>
                <th>Time Left</th>
            </tr>''')

                try:
                    adminactive = json.loads(http_get("/adminactive/{0}" . format(user)))
                    for current in adminactive:
                        req.write('''
            <tr>
                <td>{0}</td>
                <td>{1}</td>
                <td>{2}</td>
                <td>{3}</td>
                <td>{4}</td>
            </tr>''' . format(current['user'],
                            current['app'],
                            current['ip'],
                            current['timestamp'],
                            current['timeleft']))
                    req.write('''
        </table>
        <br><br>''')
                except:
                    pass

# write connection history
        req.write('''
        <table>
            <caption>Connection History</caption>
            <tr>
                <th>App</th>
                <th>IP Request From</th>
                <th>IP Request For</th>
                <th>Timestamp</th>
                <th>Time Left</th>
                <th>Comment</th>
            </tr>''')

        for connection in json.loads(http_get("/history?user={0}" . format(user))):
            timeleft = connection['timeleft']
            if timeleft is False:
                req.write('''
            <tr bgcolor='lightred'>''')
            elif connection['active']:
                req.write('''
            <tr bgcolor='lightgreen'>''')
            else:
                req.write('''
            <tr>''')

                timeleft = '''
                    <form method="POST">
                        <input type="hidden" name="ip" value={0}>
                        <input type="hidden" name="app" value="{1}">
                        <input type="hidden" name="comment" value="re{2}">
                        <input type="submit" value="re-enable">
                    </form>''' . format(connection['firewall_ip'],
                                    connection['app'],
                                    connection['timestamp'])

            req.write('''
                <td>{0}</td>
                <td>{1}</td>
                <td>{2}</td>
                <td>{3}</td>
                <td>{4}</td>
                <td>{5}</td>
            </tr>''' . format(connection['app'],
                            connection['firewall_ip'],
                            connection['user_ip'],
                            connection['timestamp'],
                            timeleft,
                            connection['comment']))
        req.write('''
        </table>
        <br><br>''')

# if admin, write everyone's history
        if admin:
            req.write('''
        <table>
            <caption>Everyone's Connection History</caption>
            <tr>
                <th>User</th>
                <th>App</th>
                <th>IP Request From</th>
                <th>IP Request For</th>
                <th>Timestamp</th>
                <th>Time Left</th>
                <th>Comment</th>
            </tr>''')

            for connection in json.loads(http_get("/history")):
                timeleft = connection['timeleft']
                if timeleft is False:
                    req.write('''
            <tr bgcolor='lightred'>''')
                elif connection['active']:
                        req.write('''
            <tr bgcolor='lightgreen'>''')
                else:
                    req.write('''
            <tr>''')

                timeleft = '''
                    <form method="POST">
                        <input type="hidden" name="ip" value={0}>
                        <input type="hidden" name="app" value="{1}">
                        <input type="hidden" name="comment" value="re{2}">
                        <input type="submit" value="re-enable">
                    </form>''' . format(connection['firewall_ip'],
                                    connection['app'],
                                    connection['timestamp'])

                req.write('''
                <td>{0}</td>
                <td>{1}</td>
                <td>{2}</td>
                <td>{3}</td>
                <td>{4}</td>
                <td>{5}</td>
                <td>{6}</td>
            </tr>''' . format(connection['user'],
                            connection['app'],
                            connection['firewall_ip'],
                            connection['user_ip'],
                            connection['timestamp'],
                            timeleft,
                            connection['comment']))

            req.write('''
        </table>
        <br><br>''')

            req.write("""
    <h5><a href="bath.sh">download</a> shell script</h5>
</html>
""")
        else:
            req.content_type = 'text/plain'
            req.write(message)


#################################################
# returns html and header with css and all that #
#################################################
def get_html_header():
    return """
<html>
  <head>
    <link href="style.css" rel="stylesheet" type="text/css">
  </head>
<body>"""
