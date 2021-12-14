import pathlib
import sys; sys.path.append(pathlib.Path(__file__).parent.parent.parent.resolve())

import pathlib
from unittest import TestCase
import os
import shutil
from zipfile import ZipFile

from wordnet.nlp import persistence


class WorkSpaceManagerTests(TestCase):

    WD = './temp'

    @classmethod
    def setUpClass(cls):
        os.mkdir(cls.WD)

    def test_SaveMany_FilesAreCreatedInWD(self):
        # Arrange
        contents = ["A", "B", "C"]

        # Act
        fileNames = persistence.WorkspaceManager(wd=self.WD).save_many(contents)

        # Assert
        for fileName, content in zip(fileNames, contents):
            path = os.path.join(self.WD, fileName)
            file = open(path, 'r')
            self.assertEqual(file.read(), content)
            file.close()

    def test_Clear_OnlyManagedFilesAreRemoved(self):
        # Arrange
        contents = ["A", "B", "C"]
        unmanagedFileName = os.path.join(self.WD, "UnmanagedFile.txt")
        open(unmanagedFileName, 'w').close()
        sut = persistence.WorkspaceManager(wd=self.WD)

        # Act
        fileNames = sut.save_many(contents)
        sut.clear()

        # Assert
        for fileName, content in zip(fileNames, contents):
            path = os.path.join(self.WD, fileName)
            self.assertFalse(os.path.exists(path))
        self.assertTrue(os.path.exists(unmanagedFileName))

    def test_Compress_ManyFiles_FilesAreZipped(self):
        # Arrange
        sut = persistence.WorkspaceManager(wd=self.WD)

        # Act
        fileName1 = sut.save("ABC")
        fileName2 = sut.save("XYZ".encode("utf-8"), ext='.bin')
        archive = sut.compress([fileName1, fileName2])

        # Assert
        with ZipFile(os.path.join(self.WD, archive)) as zipFile:
            self.assertSequenceEqual(
                [fileName1, fileName2],
                list(map(
                    lambda x: str(pathlib.Path(os.path.join(self.WD, x.filename)).resolve()),
                    zipFile.infolist())))

    def test_Decompress_Archive_FilesAreDecompressed(self):
        # Arrange
        archive = os.path.join(self.WD, 'archive.zip')
        fileName = 'file.txt'
        with ZipFile(archive, 'w') as zipFile:
            zipFile.writestr(fileName, 'Content')
        sut = persistence.WorkspaceManager(wd=self.WD)

        # Act
        decompressed = sut.decompress(archive)

        # Assert
        fileName = str(pathlib.Path(os.path.join(self.WD, fileName)).resolve())
        self.assertSequenceEqual(decompressed, [fileName])
        with open(fileName, 'r') as f:
            self.assertEqual('Content', f.read())

    def test_Clear_ManagedFileIsRemoved_NonexistentFileIsIgnored(self):
        # Act
        sut = persistence.WorkspaceManager(wd=self.WD)
        fileName = sut.save("ABC".encode("utf-8"))
        os.remove(fileName)

        # Assert
        sut.clear()
        self.assertTrue(True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.WD, ignore_errors=True)
