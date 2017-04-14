from PyQt5 import QtCore, QtGui, QtWidgets
import fa
from fa.replay import replay
from fa.wizards import WizardSC
import util

from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest

from games.gameitem import GameItem, GameItemDelegate
from model.game import GameState
from coop.coopmapitem import CoopMapItem, CoopMapItemDelegate
from games.hostgamewidget import HostgameWidget
from ui.busy_widget import BusyWidget
from fa import factions
import random
import fa
import modvault
import os

import logging
logger = logging.getLogger(__name__)


FormClass, BaseClass = util.THEME.loadUiType("coop/coop.ui")


class CoopWidget(FormClass, BaseClass, BusyWidget):
    def __init__(self, client, gameset, *args, **kwargs):
        
        BaseClass.__init__(self, *args, **kwargs)        
        
        self.setupUi(self)

        self.client = client
        
        #Ranked search UI
        self.ispassworded = False
        self.loaded = False
        
        self.coop = {}
        self.cooptypes = {}
        self.games = {}
        
        self.options = []
        
        self.client.lobby_info.coopInfo.connect(self.processCoopInfo)

        gameset.newLobby.connect(self._addGame)
        self._addExistingGames(gameset)

        self.coopList.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.coopList.setItemDelegate(CoopMapItemDelegate(self))

        self.gameList.setItemDelegate(GameItemDelegate(self))
        self.gameList.itemDoubleClicked.connect(self.gameDoubleClicked)

        self.coopList.itemDoubleClicked.connect(self.coopListDoubleClicked)
        self.coopList.itemClicked.connect(self.coopListClicked)
        
        self.client.lobby_info.coopLeaderBoard.connect(self.processLeaderBoardInfos)
        self.tabLeaderWidget.currentChanged.connect(self.askLeaderBoard)
        
        self.linkButton.clicked.connect(self.linkVanilla)
        self.leaderBoard.setVisible(0)
        self.FORMATTER_LADDER        = str(util.THEME.readfile("coop/formatters/ladder.qthtml"))
        self.FORMATTER_LADDER_HEADER = str(util.THEME.readfile("coop/formatters/ladder_header.qthtml"))

        util.THEME.setStyleSheet(self.leaderBoard, "coop/formatters/style.css")

        self.leaderBoardTextGeneral.anchorClicked.connect(self.openUrl)
        self.leaderBoardTextOne.anchorClicked.connect(self.openUrl)
        self.leaderBoardTextTwo.anchorClicked.connect(self.openUrl)
        self.leaderBoardTextThree.anchorClicked.connect(self.openUrl)
        self.leaderBoardTextFour.anchorClicked.connect(self.openUrl)

        self.replayDownload = QNetworkAccessManager()
        self.replayDownload.finished.connect(self.finishRequest)

        self.selectedItem = None

    def _addExistingGames(self, gameset):
        for game in gameset:
            if game.state == GameState.OPEN:
                self._addGame(game)

    @QtCore.pyqtSlot(QtCore.QUrl)
    def openUrl(self, url):
        self.replayDownload.get(QNetworkRequest(url))

    def finishRequest(self, reply):
        faf_replay = QtCore.QFile(os.path.join(util.CACHE_DIR, "temp.fafreplay"))
        faf_replay.open(QtCore.QIODevice.WriteOnly | QtCore.QIODevice.Truncate)                
        faf_replay.write(reply.readAll())
        faf_replay.flush()
        faf_replay.close()  
        replay(os.path.join(util.CACHE_DIR, "temp.fafreplay"))
        
    def processLeaderBoardInfos(self, message):
        ''' Process leaderboard'''

        values = message["leaderboard"]
        table = message["table"]
        if table == 0:
            w = self.leaderBoardTextGeneral
        elif table == 1:
            w = self.leaderBoardTextOne
        elif table == 2:
            w = self.leaderBoardTextTwo
        elif table == 3:
            w = self.leaderBoardTextThree
        elif table == 4:
            w = self.leaderBoardTextFour

                        
        doc = QtGui.QTextDocument()
        doc.addResource(3, QtCore.QUrl("style.css"), self.leaderBoard.styleSheet() )
        html = ("<html><head><link rel='stylesheet' type='text/css' href='style.css'></head><body>")
        
        if self.selectedItem:
            html += '<p class="division" align="center">'+self.selectedItem.name+'</p><hr/>'
        html +="<table class='players' cellspacing='0' cellpadding='0' width='630' height='100%'>"

        formatter = self.FORMATTER_LADDER
        formatter_header = self.FORMATTER_LADDER_HEADER
        cursor = w.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        w.setTextCursor(cursor) 
        color = "lime"
        line = formatter_header.format(rank="rank", names="names", time="time", color=color)
        html += line
        rank = 1
        for val in values :
            #val = values[uid]
            players = ", ".join(val["players"]) 
            numPlayers = str(len(val["players"]))
            timing = val["time"]
            gameuid = str(val["gameuid"])
            if val["secondary"] == 1:
                secondary = "Yes"
            else:
                secondary = "No"
            if rank % 2 == 0 :
                line = formatter.format(rank=str(rank), numplayers=numPlayers, gameuid=gameuid, players= players, objectives=secondary, timing=timing, type="even")
            else :
                line = formatter.format(rank=str(rank), numplayers=numPlayers, gameuid=gameuid, players= players, objectives=secondary, timing=timing, type="")
            
            rank = rank + 1
            
            html += line

        html +="</tbody></table></body></html>"

        doc.setHtml(html)
        w.setDocument(doc)
        
        self.leaderBoard.setVisible(True)
    
    @QtCore.pyqtSlot()
    def linkVanilla(self):    
        WizardSC(self).exec_()

    def busy_entered(self):
        if not self.loaded:
            self.client.lobby_connection.send(dict(command="coop_list"))
            self.loaded = True

    def askLeaderBoard(self):
        ''' 
        ask the server for stats
        '''
        if self.selectedItem:
            self.client.statsServer.send(dict(command="coop_stats", mission=self.selectedItem.uid, type=self.tabLeaderWidget.currentIndex()))

    def coopListClicked(self, item):
        '''
        Hosting a coop event
        '''
        if not hasattr(item, "mapUrl") :
            if item.isExpanded():
                item.setExpanded(False)
            else:
                item.setExpanded(True)
            return

        if item != self.selectedItem: 
            self.selectedItem = item
            self.client.statsServer.send(dict(command="coop_stats", mission=item.uid, type=self.tabLeaderWidget.currentIndex()))

    def coopListDoubleClicked(self, item):
        '''
        Hosting a coop event
        '''
        if not hasattr(item, "mapUrl") :
            return
        
        if not fa.instance.available():
            return
            
        self.client.games.stopSearchRanked()
        
        # A simple Hosting dialog.
        if fa.check.check("coop"):
            hostgamewidget = HostgameWidget(self, item, iscoop=True)
            hostgamewidget.exec_()


    @QtCore.pyqtSlot(dict)
    def processCoopInfo(self, message): 
        '''
        Slot that interprets and propagates coop_info messages into the coop list 
        ''' 
        uid = message["uid"]
      
        
        if uid not in self.coop:
            typeCoop = message["type"]
            
            if not typeCoop in self.cooptypes:
                root_item = QtWidgets.QTreeWidgetItem()
                self.coopList.addTopLevelItem(root_item)
                root_item.setText(0, "<font color='white' size=+3>%s</font>" % typeCoop)
                self.cooptypes[typeCoop] = root_item
                root_item.setExpanded(False)
            else:
                root_item = self.cooptypes[typeCoop] 
            
            itemCoop = CoopMapItem(uid, self)
            itemCoop.update(message)
            
            root_item.addChild(itemCoop)

            self.coop[uid] = itemCoop


    @QtCore.pyqtSlot(object)
    def _addGame(self, game):
        '''
        Slot that interprets and propagates games into GameItems
        '''
        if game.featured_mod != "coop":
            return

        game_item = GameItem(game)

        self.games[game] = game_item
        game.gameClosed.connect(self._removeGame)
        game.newState.connect(self._newGameState)

        game_item.update()
        self.gameList.addItem(game_item.widget)

    def _removeGame(self, game):
        self.gameList.takeItem(self.gameList.row(self.games[game].widget))

        game.gameClosed.disconnect(self._removeGame)
        game.newState.disconnect(self._newGameState)
        del self.games[game]

    def _newGameState(self, game):
        if game.state != GameState.OPEN:
            self._removeGame(game)

    @QtCore.pyqtSlot(QtWidgets.QListWidgetItem)
    def gameDoubleClicked(self, item):
        '''
        Slot that attempts to join a game.
        '''
        if not fa.instance.available():
            return

        game = [g for g in self.games.keys() if self.games[g].widget is item]
        if not game:
            return
        game = game[0]

        if not fa.check.check(game.featured_mod, game.mapname, None, game.sim_mods):
            return

        if game.password_protected:
            passw, ok = QtWidgets.QInputDialog.getText(self.client, "Passworded game" , "Enter password :", QtWidgets.QLineEdit.Normal, "")
            if ok:
                self.client.join_game(uid=game.uid, password=passw)
        else :
            self.client.join_game(uid=game.uid)


