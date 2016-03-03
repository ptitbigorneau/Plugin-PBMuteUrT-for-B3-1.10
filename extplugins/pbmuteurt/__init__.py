# -*- coding: utf-8 -*-
#
# PBMuteUrT For Urban Terror plugin for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2015 PtitBigorneau - www.ptitbigorneau.fr
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA

__author__  = 'PtitBigorneau www.ptitbigorneau.fr'
__version__ = '1.2'

import b3
import b3.plugin
import b3.events
import b3.cron
from b3.functions import getCmd

import datetime, time, calendar, threading, thread
from time import gmtime, strftime

def cdate():
        
    time_epoch = time.time() 
    time_struct = time.gmtime(time_epoch)
    date = time.strftime('%Y-%m-%d %H:%M:%S', time_struct)
    mysql_time_struct = time.strptime(date, '%Y-%m-%d %H:%M:%S')
    cdate = calendar.timegm( mysql_time_struct)

    return cdate

class PbmuteurtPlugin(b3.plugin.Plugin):
    
    _cronTab = None
    _adminPlugin = None
    _maxitempmute = "1d"
	
    def onLoadConfig(self):

        self._maxitempmute = self.getSetting('settings', 'maxitempmute', b3.STRING, self._maxitempmute)

    def onStartup(self):

        self._adminPlugin = self.console.getPlugin('admin')
        
        if not self._adminPlugin:

            self.error('Could not find admin plugin')
            return False
        
        self.registerEvent('EVT_CLIENT_AUTH', self.onClientAuth)
        self.registerEvent('EVT_GAME_MAP_CHANGE', self.onGameMapChange)

        if 'commands' in self.config.sections():
            for cmd in self.config.options('commands'):
                level = self.config.get('commands', cmd)
                sp = cmd.split('-')
                alias = None
                if len(sp) == 2:
                    cmd, alias = sp

                func = getCmd(self, cmd)
                if func:
                    self._adminPlugin.registerCommand(self, cmd, level, func, alias)

        if self._cronTab:
        
            self.console.cron - self._cronTab

        self._cronTab = b3.cron.PluginCronTab(self, self.update, minute='*/1')
        self.console.cron + self._cronTab

    def onClientAuth(self, event):

        sclient = event.client

        cursor = self.console.storage.query("""
        SELECT *
        FROM pbmuteurt n 
        WHERE n.client_id = %s       
        """ % (sclient.id))

        if cursor.rowcount != 0:

            self.console.say('%s ^3is muted'%(sclient.exactName))
            self.console.write('mute %s' % (sclient.cid))

            cursor.close()

        else:

            cursor.close()
            return False

    def onGameMapChange(self, event):

        for c in self.console.clients.getList():
                    
            cursor = self.console.storage.query("""
            SELECT *
            FROM pbmuteurt n 
            WHERE n.client_id = %s       
            """ % (c.id))

            if cursor.rowcount != 0:
                        
                self.console.say('%s ^3is muted'%(c.exactName))
                self.console.write('mute %s' % (c.cid))

            cursor.close() 
                   
    def update(self):

        cursor = self.console.storage.query("""
        SELECT *
        FROM pbmuteurt n 
        """)
                      
        c = 1
        
        if cursor.EOF:
  
            cursor.close()            
            
            return False

        while not cursor.EOF:
            
            sr = cursor.getRow()

            cclient = sr['client_id']
            datefin = sr['datefin']
            datenow = cdate()       

            if  datefin != 0:

                self.debug('%s - %s'%(datefin, datenow))
                if int(datefin) < int(datenow):
                    
                    cursor = self.console.storage.query("""
                    DELETE FROM pbmuteurt
                    WHERE client_id = '%s'
                    """ % (cclient))
                    cursor.close()
                    
                    for c in self.console.clients.getList():

                        if c.id == cclient:

                            self.console.say('%s ^3is now unmuted'%(c.exactName))
                            self.console.write('mute %s' % (c.cid))
             
            cursor.moveNext()
        cursor.close()

    def cmd_pbpermmute(self, data, client, cmd=None):

        """\
        <name / @id> [<reason>] - mute a player permanently
        """
        
        if data:
            
            input = self._adminPlugin.parseUserCmd(data)
        
        else:
        
            client.message('!pbpermmute  <name / @id> <reason>')
            return False
        
        sclient = self._adminPlugin.findClientPrompt(input[0], client)
        
        if not sclient:
            return False
        
        if sclient.maxLevel >= client.maxLevel:

            client.message('^3You don\'t have enought privileges to mute %s!' %(sclient.exactName))
            return False
        
        if input[1]:

            reason  = input[1]   
   
        else:

            reason = "Reason by ^2%s^7"%(client.name)

        if sclient:
            
            cdatefin = 0
            cdatedebut = cdate()

            cursor = self.console.storage.query("""
            SELECT *
            FROM pbmuteurt n 
            WHERE n.client_id = %s       
            """ % (sclient.id))

            if cursor.rowcount != 0:
 
                sr = cursor.getRow()

                craison = sr['raison']
                cadmin = sr['admin']
                datefin = sr['datefin']
  
                if datefin == 0:

                    mduree = 'Never'

                else:
        
                    time_struct = time.localtime(datefin)
                    mduree = time.strftime('%Y-%m-%d %H:%M:%S', time_struct)

                admin = self._adminPlugin.findClientPrompt("@"+str(cadmin), client)
                client.message('%s ^3has already been muted by^7 %s'%(sclient.exactName, admin.exactName))
                client.message('^3Reason : ^5%s^7'%(craison))
                client.message('^3Expiration : ^5%s^7'%(mduree))
                
                cursor.close()

                if mduree != 'Never':

                    client.message('%s is now muted permanently'%(sclient.exactName))
                    sclient.message('^1You are now muted permanently by %s'%(client.exactName))
                    sclient.message('^3Reason : ^1%s'%(reason))
                    
                    cursor = self.console.storage.query("""
                    UPDATE pbmuteurt
                    SET raison = '%s', admin = '%s', datedebut = '%s', datefin = '%s' 
                    WHERE client_id = '%s'
                    """ % (reason, client.id, cdatedebut, cdatefin, sclient.id))
                    cursor.close()

            else:

                self.console.write('mute %s' % (sclient.cid))
                sclient.message('^1You are muted permanently by^7 %s'%(client.exactName))
                sclient.message('^3Reason : ^5%s^7'%(reason))
                client.message('%s ^3is muted permanently^7'%(sclient.exactName))
                
                cursor.close()
            
                cursor = self.console.storage.query("""
                INSERT INTO pbmuteurt
                VALUES ('%s', '%s', '%s', '%s', '%s')
                """ % (sclient.id, reason, client.id, cdatedebut, cdatefin))
                cursor.close()
                
    def cmd_pbtempmute(self, data, client, cmd=None):

        """\
        <name / @id> <reason, duration> - mute a player temporarily
        """
        if data:
            
            input = self._adminPlugin.parseUserCmd(data)
        
        else:
        
            client.message('!pbtempmute  <name / @id> <reason, duration>')
            return False
        
        sclient = self._adminPlugin.findClientPrompt(input[0], client)
        
        if not sclient:
            return False
        
        if sclient.maxLevel >= client.maxLevel:

            client.message('^3You don\'t have enought privileges to mute %s!' %(sclient.exactName))
            return False
        
        if input[1]:

            data2 = input[1]
     
            if ',' in data2:

                data2 = data2.split(',')
                reason = data2[0]
                data2 = data2[1]
                duree = data2[:-1]

            else:

                if data2[-1:] == "d" or data2[-1:] == "h" or data2[-1:] == "m":

                    duree = data2[:-1]
                    reason = "Reason by ^2%s^7"%(client.name)
                
                else:

                    reason = data2
                    data2 = self._maxitempmute
                    duree = self._maxitempmute[:-1]

            try:

                duree = int(duree)
  
            except:
                        
                client.message('!pbtempmute  <name / @id> <reason, duration>')
                client.message('duration format xxd or xxh or xxm for xx days or xx hours or xx minutes')
                
                return False

            if data2[-1:] == "d":
                
                aduree = 'day(s)'
                sduree = duree * 86400

            elif data2[-1:] == "h":

                aduree = 'hour(s)'
                sduree = duree * 3600

            elif data2[-1:] == "m":

                aduree = 'minute(s)'
                sduree = duree * 60
            
            else:

                client.message('!pbtempmute  <name / @id> <reason, duration>')
                client.message('duration format xxd or xxh or xxm for xx days or xx hours or xx minutes')
                return False

        else:

            client.message('!pbtempmute  <name / @id> <reason, duration>')
            return False

        if client.maxLevel == self._adminleveltempmute:

            mduree = self._maxitempmute[:-1]

            try:

                mduree = int(mduree)
  
                if self._maxitempmute[-1:] == "d":

                    maduree = 'day(s)'
                    maxduree = mduree * 86400

                elif self._maxitempmute[-1:] == "h":

                    maduree = 'hour(s)'
                    maxduree = mduree * 3600

                elif self._maxitempmute[-1:] == "m":

                    maduree = 'minute(s)'
                    maxduree = mduree * 60

                else:

                    client.message('Error ! Settings PBMuteUrT Plugin')
                    self.error('Error ! Settings PBMuteUrT Plugin format maxitempmute (d, h, m) : %s'%(self._maxitempmute))
                    return False

            except:
                        
                self.error('Error ! Settings PBMuteUrT Plugin format maxitempmute (d, h, m) : %s'%(self._maxitempmute))
                maxduree =  86400
                self._maxitempmute = "1d"

            if sduree > maxduree:

                sduree = maxduree
                adure = maduree
                client.message('^3The maximum duration allowed for tempmute : %s'%(self._maxitempmute))

        if sclient:
                    
            cdatefin = sduree + cdate()
            cdatedebut = cdate()

            cursor = self.console.storage.query("""
            SELECT *
            FROM pbmuteurt n 
            WHERE n.client_id = %s       
            """ % (sclient.id))

            if cursor.rowcount != 0:
 
                sr = cursor.getRow()

                craison = sr['raison']
                cadmin = sr['admin']
                datefin = sr['datefin']
  
                if datefin == 0:

                    mduree = 'Never'

                else:
        
                    time_struct = time.localtime(datefin)
                    mduree = time.strftime('%Y-%m-%d %H:%M:%S', time_struct)

                admin = self._adminPlugin.findClientPrompt("@"+str(cadmin), client)
                client.message('%s ^3has already been muted by^7 %s'%(sclient.exactName, admin.exactName))
                client.message('^3Reason : ^5%s^7'%(craison))
                client.message('^3Expiration : ^5%s^7'%(mduree))
                
                cursor.close()

                if mduree == 'Never':

                    if client.maxLevel > self._adminleveltempmute:
                        
                        testchangeduree = 1

                    else:

                        if cdatefin > datefin:

                            testchangedruee = 1

                        else:

                            testchangedruee = 0

                else:

                        testchangeduree = 1

                if testchangeduree == 1:

                    client.message('%s ^3is now muted for ^5%s %s^7'%(sclient.exactName, duree, aduree))
                    sclient.message('^1You are now muted for ^5%s %s ^3By %s'%(duree, aduree, client.exactName))
                    sclient.message('^3Reason : ^1%s'%(reason))
                    
                    cursor = self.console.storage.query("""
                    UPDATE pbmuteurt
                    SET raison = '%s', admin = '%s', datedebut = '%s', datefin = '%s' 
                    WHERE client_id = '%s'
                    """ % (reason, client.id, cdatedebut, cdatefin, sclient.id))
                    cursor.close()

                else:

                    client.message('^3The duration of the mute of %s has not been changed'%(sclient.exactName, duree, aduree))

            else:

                self.console.write('mute %s' % (sclient.cid))
                sclient.message('^1You are now muted for ^5%s %s ^3By %s'%(duree, aduree, client.exactName))
                sclient.message('^3Reason : ^5%s^7'%(reason))
                client.message('%s ^3is now muted for ^5%s %s'%(sclient.exactName, duree, aduree))
                
                cursor.close()
            
                cursor = self.console.storage.query("""
                INSERT INTO pbmuteurt
                VALUES ('%s', '%s', '%s', '%s', '%s')
                """ % (sclient.id, reason, client.id, cdatedebut, cdatefin))
                cursor.close()

    def cmd_pbunmute(self, data, client, cmd=None):

        """\
        <name / @id> - un_mute a player
        """

        if data:
            
            input = self._adminPlugin.parseUserCmd(data)
        
        else:
        
            client.message('!pbunmute  <name / @id>')
            return False

        sclient = self._adminPlugin.findClientPrompt(input[0], client)
        
        if sclient:
 
            cursor = self.console.storage.query("""
            SELECT *
            FROM pbmuteurt n 
            WHERE n.client_id = %s       
            """ % (sclient.id))

            if cursor.rowcount != 0:

                cursor.close()
                cursor = self.console.storage.query("""
                DELETE FROM pbmuteurt
                WHERE client_id = '%s'
                """ % (sclient.id))
                cursor.close()
                
                sclient.message('^2You are unmuted by^7 %s'%(client.exactName))
                client.message('%s ^3is unmuted^7'%(sclient.exactName))

                self.console.write('mute %s 0' % (sclient.cid))

            else:
                
                cursor.close()
                client.message('%s ^3is not muted^7'%(sclient.exactName))

        else:

            return False

    def cmd_pbinfomute(self, data, client, cmd=None):

        """\
        <name / @id> - mute info a player
        """

        if data:
            
            input = self._adminPlugin.parseUserCmd(data)
        
        else:
        
            client.message('!pbinfomute  <name / @id>')
            return False
        
        sclient = self._adminPlugin.findClientPrompt(input[0], client)
        
        if not sclient:
            return False

        if sclient:
            
            cdatefin = 0
            cdatedebut = cdate()

            cursor = self.console.storage.query("""
            SELECT *
            FROM pbmuteurt n 
            WHERE n.client_id = %s       
            """ % (sclient.id))

            if cursor.rowcount != 0:
 
                sr = cursor.getRow()

                craison = sr['raison']
                cadmin = sr['admin']
                datefin = sr['datefin']
  
                if datefin == 0:

                    mduree = 'Never'

                else:
        
                    time_struct = time.localtime(datefin)
                    mduree = time.strftime('%Y-%m-%d %H:%M', time_struct)

                admin = self._adminPlugin.findClientPrompt("@"+str(cadmin), client)
                client.message('%s ^3has already been muted by^7 %s'%(sclient.exactName, admin.exactName))
                client.message('^3Reason : ^5%s^7'%(craison))
                client.message('^3Expiration : ^5%s^7'%(mduree))
                
            else:
                
                client.message('%s ^3has not muted^7'%(sclient.exactName))

            cursor.close()