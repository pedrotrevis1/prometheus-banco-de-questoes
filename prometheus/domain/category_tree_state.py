"""Qt tree state helpers for category refreshes."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTreeWidgetItemIterator


def snapshot_checked(tree):
    if tree.topLevelItemCount() == 0:
        return None
    checked = set()
    iterator = QTreeWidgetItemIterator(tree)
    while iterator.value():
        item = iterator.value()
        if item.checkState(0) == Qt.Checked:
            checked.add(item.data(0, Qt.UserRole))
        iterator += 1
    return checked


def restore_checked(tree, checked):
    if checked is None:
        return
    iterator = QTreeWidgetItemIterator(tree)
    while iterator.value():
        item = iterator.value()
        item.setCheckState(0, Qt.Checked if item.data(0, Qt.UserRole) in checked else Qt.Unchecked)
        iterator += 1
