'''Manages the animal counts in an image or collection of images'''

import json
from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QWidget, QListWidget, QFormLayout, QLabel, QLineEdit, QToolBar, 
    QAction, QPushButton, QSpinBox, QComboBox, QMessageBox, QMenu,
    QListWidgetItem
)

from JSONTools import ObjectEncoder

class GameCountData:

    def __init__(self, species, count, repeats):
        self.species = species
        self.count = count
        self.repeats = repeats

    @property
    def unique(self):
        return self.count - self.repeats

    def __str__(self):
        return f'{self.count} {self.species}, ({self.unique} new)'

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if isinstance(other, GameCountData):
            return self.species == other.species
        elif isinstance(other, str):
            return self.species == other

    def toJSON(self):
        d = {
            'Species': self.species,
            'Count': self.count,
            'Repeats': self.repeats,
            'New': self.unique
        }
        return d


class GameCountTracker(list):
    '''Tracks on a per image basis'''

    def __init__(self):
        pass # self.counts: GameCountData = []
        
    def add(self, species, count, repeats=0):
        # if this species already exists, add to it.
        # otherwise, make a new entry

        # get first matching species in counts list
        data = next((x for x in self if x.species == species), None)

        if data is None:
            self.append(GameCountData(species, count, repeats))
        else:
            data.count += count
            data.repeats += repeats

    def removeSpecies(self, species):
        # remove the data corresponding to this species
        data = next((x for x in self if x.species == species), None)

        if data is None:
            print('you tried to remove a species that is not here, fool')
        else:
            self.remove(data)

    def __str__(self):
        s = ''
        for data in self:
            s += f'{data}\n'
        return s


class MultiGameCountTracker(dict):
    '''Tracks game counts for multiple images'''

    def __init__(self):
        self.imageCounts = {}

    def add(self, fileName, species, count, repeats):
        data = GameCountData(species, count, repeats)
        self._tryAdd(fileName, data)

    def addData(self, fileName, data: GameCountData):
        self._tryAdd(fileName, data)

    def _tryAdd(self, fileName, data: GameCountData):
        try:
            imageCount = self[fileName]
        except KeyError:
            tracker = GameCountTracker()
            tracker.add(data.species, data.count, data.repeats)
            self[fileName] = tracker
        else:
            imageCount.add(data.species, data.count, data.repeats)

    def totals(self):

        totals = dict()

        for animalList in self.values():
            for animalData in animalList:
                species = animalData.species
                uniqueCount = animalData.unique
                try:
                    totals[species] += uniqueCount
                except KeyError:
                    totals[species] = uniqueCount

        return totals

    def totalsSummary(self):
        totals = self.totals()
        s = ''

        for species, count in totals.items():
            s += f'{count} {species}\n'

        return s

    def totalsSummaryHTML(self):
        totals = self.totals()
        s = ''

        for species, count in totals.items():
            s += f'<p style="padding:0;margin:0;">{count} {species}</p>'

        return s

    def __str__(self):
        s = ''
        for fileName, animalList in self.items():
            s += f'{fileName}\n'
            for data in animalList:
                s += f'\t{data}\n'
        return s

    def toHTML(self):
        s = ''
        for fileName, animalList in self.items():
            s += f'<p>{fileName}</p>'
            s += '<ul>'
            for data in animalList:
                s += f'<li>{data}</li>'
            s += '</ul>'
        return s


class QGameCountInputForm(QWidget):

    animalAdded = pyqtSignal(GameCountData)

    def __init__(self):
        super().__init__()

        self.formLayout = QFormLayout()
        self.setLayout(self.formLayout)

        # species input
        self.speciesLabel = QLabel('Species')
        self.speciesBox = QComboBox()
        self.speciesBox.setEditable(True)
        self.speciesBox.addItem('Baboon')
        self.speciesBox.addItem('Donkey')
        self.speciesBox.addItem('Eland')
        self.speciesBox.addItem('Elephant')
        self.speciesBox.addItem('Gemsbok')
        self.speciesBox.addItem('Giraffe')
        self.speciesBox.addItem('Hartebeest')
        self.speciesBox.addItem('Horse')
        self.speciesBox.addItem('Impala')
        self.speciesBox.addItem('Jackal')
        self.speciesBox.addItem('Kudu')
        self.speciesBox.addItem('Kudu')
        self.speciesBox.addItem('Ostrich')
        self.speciesBox.addItem('Rhino')
        self.speciesBox.addItem('Springbok')
        self.speciesBox.addItem('Steenbok')
        self.speciesBox.addItem('Warthog')
        self.speciesBox.addItem('Waterbuck')
        self.speciesBox.addItem('Zebra')

        # count input
        self.countLabel = QLabel('Count')
        self.countBox = QSpinBox()

        # number of repeats input
        self.repeatsLabel = QLabel('Repeats')
        self.repeatsBox = QSpinBox()

        # ok/cancel
        self.okButton = QPushButton('Add')
        self.okButton.clicked.connect(self.addAnimalEvent)

        # add to the form
        self.formLayout.addRow(self.speciesLabel, self.speciesBox)
        self.formLayout.addRow(self.countLabel, self.countBox)
        self.formLayout.addRow(self.repeatsLabel, self.repeatsBox)
        self.formLayout.addRow(self.okButton)

    def addAnimalEvent(self):
        if self.countBox.value() == 0:
            pass
        elif self.repeatsBox.value() > self.countBox.value():
            QMessageBox.information(
                self, 'Invalid Animal Count',
                'Nope.\n'
                f'One cannot see a total of {self.countBox.value()} animals '
                f'but say that {self.repeatsBox.value()} are repeated.'
            )
        else:
            self.emitAnimalAdded()
            self.clear()

    # def keyPressEvent(self, event):
    #     key = event.key()
    #     if key == Qt.Key_Enter:
    #         self.emitAnimalAdded()
    #         self.clear()
    #     else:
    #         super().keyPressEvent(event)

    @pyqtSlot()
    def clear(self):
        self.countBox.setValue(0)
        self.repeatsBox.setValue(0)

    @pyqtSlot()
    def emitAnimalAdded(self):
        data = GameCountData(
            self.speciesBox.currentText(),
            self.countBox.value(),
            self.repeatsBox.value()
        )

        self.animalAdded.emit(data)


class QGameCountTracker(QListWidget):

    def __init__(self):
        super().__init__()

        self._appContext = None
        self.addAnimalForm = QGameCountInputForm()
        self.addAnimalForm.animalAdded.connect(self.addAnimalData)

        self.currentImageFile = ''
        self.JSONDumpFile = None
        self.summaryFile = None

        self.counts = MultiGameCountTracker()

        self.createActions()

        self.toolbar = QToolBar()
        self.initToolbar()

        self.menu = QMenu('&Tracker', self)
        self.initMenu()

    @property
    def appContext(self):
        return self._appContext

    @appContext.setter
    def appContext(self, context):
        self._appContext = context
        self.toolbar.clear()
        self.menu.clear()
        self.createActions()
        self.initToolbar()
        self.initMenu()

    @pyqtSlot(GameCountData)
    def addAnimalData(self, data):
        self.counts.addData(self.currentImageFile, data)
        self.render()

    def keyReleaseEvent(self, event):
        key = event.key()
        if key == Qt.Key_Delete:
            self.clearCurrentSelectionCountData()
        else:
            super().keyPressEvent(event)

    def load(self, fileName):
        self.JSONDumpFile = fileName
        with open(self.JSONDumpFile, 'r') as f:
            try:
                d = json.load(f)
            except json.decoder.JSONDecodeError:
                print('invalid json file')
            else:
                self.counts = self._decodeJSON(d)
            finally:
                self.render()

    def _decodeJSON(self, d: dict):

        counts = MultiGameCountTracker()

        # first is a dict of filenames paired with a list of animals
        for fileName, countList in d.items():
            
            # decode the list of animals
            for data in countList:
                gameData = GameCountData(data['Species'], data['Count'], data['Repeats'])
                counts.addData(fileName, gameData)

        return counts

    def dump(self):
        if self.JSONDumpFile is None:
            self.JSONDumpFile = Path().cwd() / Path('counts.json')

        if self.summaryFile is None:
            self.summaryFile = self.JSONDumpFile.parent / Path('count summary.txt')

        self.JSONDumpFile.touch()
        self.summaryFile.touch()
        
        with open(self.JSONDumpFile, 'w') as f:
            f.write(self.serialize())

        with open(self.summaryFile, 'w') as f:
            f.write(self.summarize())

    def summarize(self):
        s = self.counts.totalsSummary()
        s += '\n-------------------------\n'
        s += str(self.counts)
        return s

    def displaySummary(self):
        QMessageBox.about(self, 'Count Summary',
            self.counts.totalsSummaryHTML()
            + '\n-------------------------\n'
            + self.counts.toHTML())

    def serialize(self):
        return json.dumps(self.counts, cls=ObjectEncoder, indent=2, sort_keys=True)

    def clearData(self):
        # clears the internal data structure.
        # NOTE: Does NOT automatically rewrite the json file
        self.counts.clear()
        self.render()

    def clearCurrentSelectionCountData(self):
        # TODO clear the data for just the current file AND species
        fileName = self.currentImageFile
        item = self.currentItem()

        if item is not None:
            species = item.species
            self.counts[fileName].removeSpecies(species)
            self.render()

    def render(self):
        self.clear()
        try:
            tracker = self.counts[self.currentImageFile]
        except KeyError:
            pass
        else:
            for track in tracker:

                # add item and save the species for easier access later
                item = QListWidgetItem(str(track), self)
                item.species = track.species

    def createActions(self):
        if self.appContext is None:
            clearFp = './resources/eraserIcon.png'
            infoFp = './resources/infoIcon.png'
        else:
            clearFp = self.appContext.get_resource('eraserIcon.png')
            infoFp = self.appContext.get_resource('infoIcon.png')

        self.clearDataAct = QAction(QIcon(clearFp), '&Delete All Animal Counts', self, triggered=self.clearData)
        self.summarizeAct = QAction(QIcon(infoFp), '&Summarize', self, shortcut=Qt.Key_S, triggered=self.displaySummary)

    def initToolbar(self):
        self.toolbar.addAction(self.summarizeAct)

    def initMenu(self):
        self.menu.addAction(self.summarizeAct)
        self.menu.addAction(self.clearDataAct)