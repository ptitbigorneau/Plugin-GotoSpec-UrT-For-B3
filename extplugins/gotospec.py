# gotospec Plugin

__author__  = 'PtitBigorneau www.ptitbigorneau.fr'
__version__ = '1.0'

import b3
import b3.plugin
import b3.events
import b3.cron
import datetime, time, calendar, threading, thread
from time import gmtime, strftime


def cdate():
        
    time_epoch = time.time() 
    time_struct = time.gmtime(time_epoch)
    date = time.strftime('%Y-%m-%d %H:%M:%S', time_struct)
    mysql_time_struct = time.strptime(date, '%Y-%m-%d %H:%M:%S')
    cdate = calendar.timegm( mysql_time_struct)

    return cdate

class GotospecPlugin(b3.plugin.Plugin):
    
    _cronTab = None
    _adminPlugin = None


    def onStartup(self):

        self._adminPlugin = self.console.getPlugin('admin')
        
        if not self._adminPlugin:

            self.error('Could not find admin plugin')
            return False
        
        self.registerEvent(b3.events.EVT_CLIENT_TEAM_CHANGE)
        self.registerEvent(b3.events.EVT_CLIENT_CONNECT)

        self._adminPlugin.registerCommand(self, 'gotospec',self._adminlevel, self.cmd_gotospec)
        
        if self._cronTab:
        
            self.console.cron - self._cronTab

        self._cronTab = b3.cron.PluginCronTab(self, self.update, hour='*/1')
        self.console.cron + self._cronTab
    
    def onLoadConfig(self):

        self._adminlevel = self.config.get('settings', 'adminlevel')

    def onEvent(self, event):

        if (event.type == b3.events.EVT_CLIENT_TEAM_CHANGE) or (event.type == b3.events.EVT_CLIENT_CONNECT):
            
            sclient = event.client

            cursor = self.console.storage.query("""
            SELECT *
            FROM gotospec n 
            WHERE n.client_id = %s       
            """ % (sclient.id))

            if cursor.rowcount != 0:
 
                sr = cursor.getRow()
                self.cactif = sr['actif']
                self.craison = sr['raison']
                self.cadmin = sr['admin']
                self.datefin = sr['datefin']
                self.datedebut = sr['datedebut']
                cursor.close()

                self.cdate = cdate()

                if  self.datefin != 0:

                    if (self.cactif == 'yes') and (self.datefin < self.cdate):

                        cursor = self.console.storage.query("""
                        UPDATE gotospec
                        SET actif = 'no' 
                        WHERE client_id = '%s'
                        """ % (sclient.id))
                        cursor.close()
                    
                        self.cactif = 'no'
 
                if self.cactif == 'yes':

                    self.tospec(sclient)
                
            else:

                cursor.close()
                return False
    
    def update(self):

        cursor = self.console.storage.query("""
        SELECT *
        FROM gotospec n 
        """)
        
        c = 1
        
        if cursor.EOF:
  
            cursor.close()            
            
            return False

        while not cursor.EOF:
            
            sr = cursor.getRow()
            cactif = sr['actif']
            cclient = sr['client_id']
            datefin = sr['datefin']

            self.cdate = cdate()

            if  datefin != 0:

                if (cactif == 'yes') and (datefin < self.cdate):

                    cursor = self.console.storage.query("""
                    UPDATE gotospec
                    SET actif = 'no' 
                    WHERE client_id = '%s'
                    """ % (cclient))
                    cursor.close()
 
            cursor.moveNext()

    def tospec(self, sclient):

        if (sclient.team == 2) or (sclient.team == 3):

            self.console.write('forceteam %s %s' %(sclient.cid, 's'))
        
            sclient.message('^1You are locked in spectator !')
            sclient.message('^2Reason : ^1%s'%(self.craison))

    def cmd_gotospec(self, data, client, cmd=None):

        """\
        lock player in spectator
        <playername>  <playername> <reason, duration in minutes> or <reason> or <duration in minutes> or <-u>
        """
        
        if data:
            input = self._adminPlugin.parseUserCmd(data)
        
        else:
        
            client.message('!gotospec  <playername> <reason, duration in minutes> or <reason> or <duration in minutes> or <-u>')
            return False
        
        sclient = self._adminPlugin.findClientPrompt(input[0], client)
        
        if not sclient:
            return False
        
        if sclient.maxLevel >= client.maxLevel:
        
            client.message('^3Invalid Command on %s!' %(sclient.exactName))
            return False
        
        if not input[1]:
        
            cursor = self.console.storage.query("""
            SELECT *
            FROM gotospec n 
            WHERE n.client_id = %s       
            """ % (sclient.id))

            if cursor.rowcount != 0:
 
                sr = cursor.getRow()
                cactif = sr['actif']
                craison = sr['raison']
                cadmin = sr['admin']
                datefin = sr['datefin']
                datedebut = sr['datedebut']
                cursor.close()

                self.cdate = cdate()

                if cactif == 'no':

                    client.message('%s is not locked in spectator'%(sclient.exactName))                    
                    
                    return

                if datefin == 0:

                    mduree = 'Never'

                else:
        
                    time_struct = time.localtime(datefin)
                    mduree = time.strftime('%Y-%m-%d %H:%M:%S', time_struct)

                admin = self._adminPlugin.findClientPrompt("@"+str(cadmin), client)
                client.message('%s has been locked by %s'%(sclient.exactName, admin.exactName))
                client.message('Raison : %s'%(craison))
                client.message('Expiration : %s'%(mduree))

            else:
                
                client.message('%s is not locked in spectator'%(sclient.exactName))
                cursor.close()
                return False
        
        else:

            nespace= input[1].count(',')
            
            if nespace > 1:
        
                client.message('!gotospec  <playername> <reason, duration in minutes>')
                return False            
            
            if nespace == 0:

                if not input[1].isdigit():                
            
                    if input[1] != '-u':

                        craison = input[1]
                        cduree = '0'            
                    
                    else:

                        cursor = self.console.storage.query("""
                        SELECT *
                        FROM gotospec n 
                        WHERE n.client_id = %s       
                        """ % (sclient.id))

                        if cursor.rowcount != 0:
 
                            cursor.close()

                            cursor = self.console.storage.query("""
                            UPDATE gotospec
                            SET actif = 'no' 
                            WHERE client_id = '%s'
                            """ % (sclient.id))
                            cursor.close()
                            client.message('%s is no longer locked in spectator'%(sclient.exactName))
                            sclient.message('^2You are no longer locked in spectator')

                        else:

                            client.message('%s is not locked in spectator'%(sclient.exactName))
                            cursor.close()
                            return False

                else:

                    craison = client.exactName
                    cduree = input[1]   

            if nespace == 1:
        
                tdata = input[1].split(',')
                craison = tdata[0]
                cduree = tdata[1]
                
                cduree=cduree.replace(' ','')

                if not cduree.isdigit():

                    client.message('Error duration ! %s'%(cduree))
            
                    return False

                if (craison == '-u') and (craison.isdigit()):

                    client.message('Error reason !')
            
                    return False
        
            if input[1] == '-u':

                return
 
            self.console.write('forceteam %s %s' %(sclient.cid, 's'))
        
            client.message('%s is locked in spectator'%(sclient.exactName))
            sclient.message('^1You are locked in spectator !')
            sclient.message('^2Reason : ^1%s'%(craison))
            cdatedebut = cdate()
            
            if cduree == '0':

                cdatefin = 0

            else:
            
                cdatefin = int(cdate()) + int(cduree) * 60
            
            cadmin = client.id
            cactif = 'yes'
        
            cursor = self.console.storage.query("""
            SELECT *
            FROM gotospec n 
            WHERE n.client_id = %s       
            """ % (sclient.id))

            if cursor.rowcount != 0:
 
                cursor.close()

                cursor = self.console.storage.query("""
                UPDATE gotospec
                SET actif = 'yes', raison = '%s', admin = '%s', datedebut = '%s', datefin = '%s' 
                WHERE client_id = '%s'
                """ % (craison, cadmin, cdatedebut, cdatefin, sclient.id))
                cursor.close()

            else:


                cursor.close()
            
                cursor = self.console.storage.query("""
                INSERT INTO gotospec
                VALUES ('%s', '%s', '%s', '%s', '%s', '%s')
                """ % (sclient.id, craison, cadmin, 'yes', cdatedebut, cdatefin))
                cursor.close()
                return False
         
        