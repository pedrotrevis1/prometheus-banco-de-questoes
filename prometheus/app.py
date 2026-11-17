from prometheus.domain.exam_order import ExamOrder
from prometheus.domain.versions import generate_versions
from prometheus.storage.exams import fetch_ordered_questions, fetch_question_summaries
from prometheus.export.documents import build_exam_documents, exam_content_fingerprint
from prometheus.export.files import output_paths, publish_documents, PublicationError
from prometheus.export.images import inspect_question_images
from prometheus.export.images import embed_html_images, clipboard_image_data, ImageReadError
from prometheus.domain.questions import (RichContent, QuestionDraft, QuestionValidationError,
    QuestionSession, format_last_modified, split_available_categories, stored_school_years, validate_question)
from prometheus.storage.questions import get_question, insert_question, update_question
from prometheus.domain.preview import legacy_drag_height, PreviewSizing
from prometheus.domain.source_years import validate_year_range, YearRangeError
from prometheus.domain.search import SearchFilters, SearchViewState
from prometheus.storage.search import page_questions
from prometheus.storage import database as storage_database
from prometheus.storage import backup as storage_backup
from prometheus.storage import config as storage_config
from prometheus.resources import asset_path
from prometheus.domain.versions import make_version_questions
from prometheus.domain.school_years import parse_question_year_values, format_question_year_info
from prometheus.domain.richtext import html_fragment, format_equation_html

import sys
from dataclasses import replace
from datetime import datetime
import os
import sqlite3
import platform  # <--- Este é o import que estava faltando

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QTabWidget,
    QComboBox, QTextEdit, QCheckBox, QMessageBox, QScrollArea,
    QFrame, QButtonGroup, QSizePolicy, QStyledItemDelegate, QListView,
    QTreeWidget, QTreeWidgetItem, QListWidget, QDialog, QFormLayout, QToolButton, QInputDialog,
    QRadioButton, QGridLayout, QProxyStyle, QStyle, QHeaderView, QStyleFactory, QSpinBox,
    QStyleOptionComboBox, QStyleOptionSpinBox
)
from PySide6.QtCore import Qt, QByteArray, QBuffer, QIODevice, QPoint, QPointF, QRectF, QSize, QTimer, QEvent, QMimeData
from PySide6.QtGui import QFont, QPalette, QIcon, QIconEngine, QTextImageFormat, QImage, QPixmap, QTextCharFormat, QTextCursor, QPainter, QPen, QPolygon, QPainterPath, QColor

APP_NAME = "Prometheus - Banco de Questões"
from prometheus import __version__
IS_WINDOWS = platform.system() == "Windows"


def interface_font():
    """Point sizes let Qt handle the monitor's DPI without conflicting pixel sizes."""
    font = QFont("Segoe UI", 10) if IS_WINDOWS else QFont("Arial", 14)
    return font

# --- BASE THEMES ---
DARK_THEME = """
QMainWindow { background-color: #1E1E2E; color: #FFFFFF; }
QWidget { font-family: Arial; font-size: 14px; color: #E2E8F0; }
QFrame { background-color: #252538; border-radius: 8px; border: none; }
#SettingsPanel { background-color: #181825; border-right: 1px solid #313244; border-radius: 0px; }
#AltsContainer { background-color: #252538; border: 1px solid #313244; border-radius: 8px; }
QLabel { background-color: transparent; color: #E2E8F0; font-weight: 500; }
#HeaderLabel { font-size: 18px; font-weight: bold; color: #10B981; }
#CardLabel { font-weight: bold; color: #89B4FA; font-size: 12px; background-color: #294338; padding: 6px 8px; border-radius: 6px; }
#YearSegmentLabel { font-weight: bold; }
#YearSegmentDivider { background-color: #45475A; min-height: 1px; max-height: 1px; border: none; }
#FilterSectionDivider { background-color: #45475A; min-height: 3px; max-height: 3px; border: none; }
#FilterHeaderLabel { background-color: #294338; color: #A7F3D0; font-weight: bold; border-radius: 5px; padding: 5px; }
#GenerationOptionsPanel { background-color: #252538; border: 1px solid #45475A; border-radius: 10px; }
#RegisterScrollContent, #SearchFilterContent, #QuestionResultsContent { background-color: #1E1E2E; }
#GenerationSectionTitle { font-size: 16px; font-weight: bold; color: #E2E8F0; }
QLineEdit, QTextEdit, QComboBox { background-color: #313244; border: 1px solid #45475A; border-radius: 6px; padding: 8px; color: #FFFFFF; }
QSpinBox { background-color: #313244; border: 1px solid #45475A; border-radius: 6px; padding: 4px; color: #FFFFFF; }
#QuestionPreview { border: 1px solid #45475A; border-radius: 6px; padding: 0px; }
QLineEdit:focus, QTextEdit:focus, QComboBox:focus { border: 1px solid #10B981; }
QFrame#ComboPopupContainer { background-color: #313244; border: 1px solid #45475A; border-radius: 6px; }
QComboBox QListView { background-color: #313244; color: #FFFFFF; border: none; padding: 4px; margin: 0px; min-width: 100px; }
QComboBox QAbstractItemView { background-color: #313244; color: #FFFFFF; border: none; selection-background-color: #10B981; selection-color: #11111B; outline: none; }
QPushButton, QToolButton { background-color: #313244; color: #FFFFFF; border: 1px solid #45475A; border-radius: 6px; padding: 8px 16px; font-weight: bold; }
QPushButton:hover, QToolButton:hover { background-color: #45475A; }
QPushButton#SidebarUtilityButton { background-color: #252538; border: 1px solid #45475A; padding: 5px 10px; font-size: 13px; }
QPushButton#SidebarUtilityButton:hover { background-color: #3A3A50; }
QPushButton#BrowseSelectedButton:checked { background-color: #294338; color: #A7F3D0; border: 1px solid #10B981; }
QToolButton:checked { background-color: #10B981; color: #11111B; }
#FormattingToolbar { background-color: #252538; border: 1px solid #45475A; border-radius: 8px; }
#RichTextEditorPanel { background-color: #313244; border: 1px solid #45475A; border-radius: 8px; }
#RichTextEditorPanel #FormattingToolbar { background-color: transparent; border: none; border-bottom: 1px solid #45475A; border-radius: 0px; }
#RichTextEditorPanel QTextEdit { background-color: transparent; border: none; border-radius: 0px; }
#FormattingToolbar QToolButton { background-color: transparent; color: #E2E8F0; border: none; border-radius: 5px; min-width: 38px; max-width: 38px; min-height: 34px; max-height: 34px; padding: 0px; font-size: 16px; }
#FormattingToolbar QToolButton:hover { background-color: #3A3A50; }
#FormattingToolbar QToolButton:checked { background-color: #10B981; color: #11111B; }
#FormattingToolbar QToolButton#InsertToolButton { min-width: 40px; max-width: 40px; font-size: 18px; }
#ToolbarSeparator { background-color: #45475A; border: none; max-width: 1px; min-width: 1px; }
QPushButton#PrimaryButton { background-color: #10B981; color: #11111B; border: none; }
QPushButton#PrimaryButton:hover { background-color: #0D9488; }
QPushButton#DangerButton { background-color: #F38BA8; color: #11111B; border: none; }
QPushButton#DangerButton:hover { background-color: #E64553; }
QTabWidget::pane { border: 1px solid #313244; border-radius: 8px; background-color: #1E1E2E; top: -1px; }
QTabBar::tab { background-color: #313244; color: #A6ADC8; padding: 10px 20px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
QTabBar::tab:selected { background-color: #1E1E2E; color: #10B981; border: 1px solid #313244; border-bottom-color: #1E1E2E; font-weight: bold; }
QCheckBox { spacing: 8px; }
QCheckBox:disabled, QLabel:disabled { color: #7F849C; }
QSpinBox:disabled { background-color: #252538; border-color: #45475A; color: #7F849C; }
QTreeWidget { background-color: #313244; border: 1px solid #45475A; border-radius: 6px; color: #FFFFFF; padding: 5px; }
QTreeWidget::item { padding: 6px; border-radius: 4px; }
QTreeWidget::item:hover { background-color: #3F4057; }
QTreeWidget::item:selected { background-color: #45475A; color: #10B981; font-weight: bold; }
QScrollArea { border: none; background-color: transparent; }
QScrollBar:vertical { border: none; background: #1E1E2E; width: 10px; border-radius: 5px; }
QScrollBar::handle:vertical { background: #45475A; min-height: 20px; border-radius: 5px; }
QScrollBar::handle:vertical:hover { background: #10B981; }
QMessageBox, QInputDialog { background-color: #1E1E2E; }
QMessageBox QLabel, QInputDialog QLabel { color: #E2E8F0; }
QMessageBox QPushButton, QInputDialog QPushButton { background-color: #313244; color: #FFFFFF; border: 1px solid #45475A; border-radius: 6px; padding: 6px 16px; }
QMessageBox QPushButton:hover, QInputDialog QPushButton:hover { background-color: #45475A; }
"""

LIGHT_THEME = """
QMainWindow { background-color: #F8FAFC; color: #0F172A; }
QWidget { background-color: #F8FAFC; font-family: Arial; font-size: 14px; color: #334155; }
QFrame { background-color: #FFFFFF; border-radius: 8px; border: none; }
#SettingsPanel { background-color: #F1F5F9; border-right: 1px solid #CBD5E1; border-radius: 0px; }
#AltsContainer { background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 8px; }
QLabel { background-color: transparent; color: #334155; font-weight: 500; }
#HeaderLabel { font-size: 18px; font-weight: bold; color: #059669; }
#CardLabel { font-weight: bold; color: #2563EB; font-size: 12px; background-color: #DCFCE7; padding: 6px 8px; border-radius: 6px; }
#YearSegmentLabel { font-weight: bold; }
#YearSegmentDivider { background-color: #CBD5E1; min-height: 1px; max-height: 1px; border: none; }
#FilterSectionDivider { background-color: #CBD5E1; min-height: 3px; max-height: 3px; border: none; }
#FilterHeaderLabel { background-color: #DCFCE7; color: #166534; font-weight: bold; border-radius: 5px; padding: 5px; }
#GenerationOptionsPanel { background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 10px; }
#RegisterScrollContent, #SearchFilterContent, #QuestionResultsContent { background-color: #F8FAFC; }
#GenerationSectionTitle { font-size: 16px; font-weight: bold; color: #334155; }
QLineEdit, QTextEdit, QComboBox { background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px; padding: 8px; color: #0F172A; }
QSpinBox { background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px; padding: 4px; color: #0F172A; }
#QuestionPreview { border: 1px solid #CBD5E1; border-radius: 6px; padding: 0px; }
QLineEdit:focus, QTextEdit:focus, QComboBox:focus { border: 1px solid #059669; }
QFrame#ComboPopupContainer { background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px; }
QComboBox QListView { background-color: #FFFFFF; color: #0F172A; border: none; padding: 4px; margin: 0px; min-width: 100px; }
QComboBox QAbstractItemView { background-color: #FFFFFF; color: #0F172A; border: none; selection-background-color: #059669; selection-color: #FFFFFF; outline: none; }
QPushButton, QToolButton { background-color: #FFFFFF; color: #334155; border: 1px solid #CBD5E1; border-radius: 6px; padding: 8px 16px; font-weight: bold; }
QPushButton:hover, QToolButton:hover { background-color: #F1F5F9; }
QPushButton#SidebarUtilityButton { background-color: #FFFFFF; border: 1px solid #CBD5E1; padding: 5px 10px; font-size: 13px; }
QPushButton#SidebarUtilityButton:hover { background-color: #E2F4E9; }
QPushButton#BrowseSelectedButton:checked { background-color: #DCFCE7; color: #047857; border: 1px solid #059669; }
QToolButton:checked { background-color: #059669; color: #FFFFFF; }
#FormattingToolbar { background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 8px; }
#RichTextEditorPanel { background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 8px; }
#RichTextEditorPanel #FormattingToolbar { background-color: transparent; border: none; border-bottom: 1px solid #CBD5E1; border-radius: 0px; }
#RichTextEditorPanel QTextEdit { background-color: transparent; border: none; border-radius: 0px; }
#FormattingToolbar QToolButton { background-color: transparent; color: #475569; border: none; border-radius: 5px; min-width: 38px; max-width: 38px; min-height: 34px; max-height: 34px; padding: 0px; font-size: 16px; }
#FormattingToolbar QToolButton:hover { background-color: #F1F5F9; }
#FormattingToolbar QToolButton:checked { background-color: #D1FAE5; color: #047857; }
#FormattingToolbar QToolButton#InsertToolButton { min-width: 40px; max-width: 40px; font-size: 18px; }
#ToolbarSeparator { background-color: #CBD5E1; border: none; max-width: 1px; min-width: 1px; }
QPushButton#PrimaryButton { background-color: #059669; color: #FFFFFF; border: none; }
QPushButton#PrimaryButton:hover { background-color: #047857; }
QPushButton#DangerButton { background-color: #EF4444; color: #FFFFFF; border: none; }
QPushButton#DangerButton:hover { background-color: #DC2626; }
QTabWidget::pane { border: 1px solid #CBD5E1; border-radius: 8px; background-color: #F8FAFC; top: -1px; }
QTabBar::tab { background-color: #E2E8F0; color: #64748B; padding: 10px 20px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
QTabBar::tab:selected { background-color: #F8FAFC; color: #059669; border: 1px solid #CBD5E1; border-bottom-color: #F8FAFC; font-weight: bold; }
QCheckBox { background-color: transparent; color: #334155; spacing: 8px; }
QCheckBox:disabled, QLabel:disabled { color: #94A3B8; }
QSpinBox:disabled { background-color: #F1F5F9; border-color: #CBD5E1; color: #94A3B8; }
QRadioButton { background-color: transparent; color: #334155; spacing: 8px; }
QTreeWidget { background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px; color: #0F172A; padding: 5px; }
QTreeWidget::item { padding: 6px; border-radius: 4px; }
QTreeWidget::item:hover { background-color: #F1F5F9; }
QTreeWidget::item:selected { background-color: #E2E8F0; color: #059669; font-weight: bold; }
QScrollArea { border: none; background-color: #F8FAFC; }
QScrollBar:vertical { border: none; background: #F8FAFC; width: 10px; border-radius: 5px; }
QScrollBar::handle:vertical { background: #CBD5E1; min-height: 20px; border-radius: 5px; }
QScrollBar::handle:vertical:hover { background: #059669; }
QMessageBox, QInputDialog { background-color: #F8FAFC; }
QMessageBox QLabel, QInputDialog QLabel { color: #334155; }
QMessageBox QPushButton, QInputDialog QPushButton { background-color: #FFFFFF; color: #334155; border: 1px solid #CBD5E1; border-radius: 6px; padding: 6px 16px; }
QMessageBox QPushButton:hover, QInputDialog QPushButton:hover { background-color: #F1F5F9; }
"""

def windows_theme(base_theme, dark=False):
    """Shared Windows metrics for every screen and dialog, in both themes."""
    colors = {
        "bg": "#1E1E2E" if dark else "#F8FAFC",
        "surface": "#292A3D" if dark else "#FFFFFF",
        "border": "#45475A" if dark else "#CBD5E1",
        "text": "#E2E8F0" if dark else "#334155",
        "muted": "#A6ADC8" if dark else "#64748B",
        "hover": "#36384D" if dark else "#F1F5F9",
        "accent": "#10B981" if dark else "#059669",
        "accent_hover": "#34D399" if dark else "#047857",
        "tint": "#294338" if dark else "#E8F5EF",
        "tint_text": "#A7F3D0" if dark else "#166534",
        "on_accent": "#11111B" if dark else "#FFFFFF",
        "danger": "#F38BA8" if dark else "#DC3545",
        "danger_hover": "#F5A3B9" if dark else "#BE2636",
    }
    # Appended selectors override the original platform-neutral theme. Specific
    # selectors also cover nested editors and dialog buttons in that theme.
    return base_theme + """
    QWidget { font-family: "Segoe UI"; font-size: 10pt; }
    QDialog { background: %(bg)s; color: %(text)s; }
    QLabel { font-weight: 400; }
    #HeaderLabel { font-size: 12pt; font-weight: 600; }
    #GenerationSectionTitle { font-size: 11pt; font-weight: 600; }
    #CardLabel { font-size: 9pt; font-weight: 600; color: %(text)s; background: %(tint)s;
        padding: 5px 8px; border-radius: 4px; }
    #YearSegmentLabel { font-weight: 600; }
    #FilterHeaderLabel { background: %(tint)s; color: %(tint_text)s;
        font-size: 10pt; font-weight: 600; padding: 3px 8px; border-radius: 4px; }
    #FilterSectionDivider { min-height: 1px; max-height: 1px; background: %(border)s; }
    QLineEdit, QComboBox, QSpinBox { background: %(surface)s; color: %(text)s;
        border: 1px solid %(border)s; border-radius: 4px; padding: 4px 8px;
        min-height: 20px; selection-background-color: %(accent)s;
        selection-color: %(on_accent)s; }
    QTextEdit { background: %(surface)s; color: %(text)s; border: 1px solid %(border)s;
        border-radius: 4px; padding: 6px; selection-background-color: %(accent)s;
        selection-color: %(on_accent)s; }
    QLineEdit, QTextEdit { placeholder-text-color: %(muted)s; }
    QLineEdit:hover, QTextEdit:hover, QComboBox:hover, QSpinBox:hover { border-color: %(muted)s; }
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus { border-color: %(accent)s; }
    QLineEdit:disabled, QTextEdit:disabled, QComboBox:disabled, QSpinBox:disabled {
        background: %(bg)s; color: %(muted)s; border-color: %(border)s; }
    QComboBox { padding-right: 27px; }
    QComboBox::drop-down { subcontrol-origin: border; subcontrol-position: top right;
        width: 24px; border: none; background: transparent; }
    QComboBox::down-arrow { image: none; }
    QSpinBox { padding-right: 24px; }
    QSpinBox::up-button { subcontrol-origin: border; subcontrol-position: top right;
        width: 20px; border: none; border-top-right-radius: 4px; }
    QSpinBox::down-button { subcontrol-origin: border; subcontrol-position: bottom right;
        width: 20px; border: none; border-bottom-right-radius: 4px; }
    QSpinBox::up-arrow, QSpinBox::down-arrow { image: none; }
    QSpinBox::up-button:hover, QSpinBox::down-button:hover { background: %(hover)s; }
    QComboBox QListView { padding: 3px; font-size: 10pt; }
    QComboBox QAbstractItemView::item { padding: 4px 7px; min-height: 20px; }
    QPushButton, QToolButton, QMessageBox QPushButton, QInputDialog QPushButton {
        background: %(surface)s; color: %(text)s; border: 1px solid %(border)s;
        border-radius: 4px; padding: 4px 12px; min-height: 20px; font-weight: 600; }
    QPushButton:hover, QToolButton:hover, QMessageBox QPushButton:hover,
    QInputDialog QPushButton:hover { background: %(hover)s; border-color: %(muted)s; }
    QPushButton:pressed, QToolButton:pressed { background: %(tint)s; }
    QPushButton:focus, QToolButton:focus { border-color: %(accent)s; }
    QPushButton:disabled, QToolButton:disabled { color: %(muted)s;
        background: %(bg)s; border-color: %(border)s; }
    QPushButton#SidebarUtilityButton { font-size: 10pt; padding: 4px 10px; }
    QPushButton#PrimaryButton { background: %(accent)s; color: %(on_accent)s;
        border: 1px solid %(accent)s; }
    QPushButton#PrimaryButton:hover { background: %(accent_hover)s; border-color: %(accent_hover)s; }
    QPushButton#PrimaryButton:pressed { background: %(accent_hover)s; }
    QPushButton#PrimaryButton:disabled, QPushButton#DangerButton:disabled {
        background: %(hover)s; color: %(muted)s; border-color: %(border)s; }
    QPushButton#DangerButton { background: %(danger)s; color: %(on_accent)s;
        border: 1px solid %(danger)s; }
    QPushButton#DangerButton:hover { background: %(danger_hover)s; border-color: %(danger_hover)s; }
    QPushButton#PrimaryButton:focus, QPushButton#DangerButton:focus { border-color: %(text)s; }
    #RichTextEditorPanel, #FormattingToolbar, #AltsContainer, #GenerationOptionsPanel {
        border-radius: 5px; }
    #RichTextEditorPanel { background: %(surface)s; }
    #RichTextEditorPanel #FormattingToolbar { background: transparent; }
    #RichTextEditorPanel QTextEdit { background: transparent; padding: 6px; }
    #FormattingToolbar QToolButton, #FormattingToolbar QToolButton#InsertToolButton {
        min-width: 30px; max-width: 30px; min-height: 28px; max-height: 28px;
        padding: 0; border: none; border-radius: 3px; font-size: 10pt; }
    #FormattingToolbar QToolButton:hover { background: %(hover)s; }
    #FormattingToolbar QToolButton:checked { background: %(tint)s; color: %(tint_text)s; }
    #FormattingToolbar QToolButton:focus { border: 1px solid %(accent)s; }
    QTabBar::tab { font-size: 10pt; font-weight: 400; padding: 7px 16px;
        border: 1px solid transparent; border-top-left-radius: 5px; border-top-right-radius: 5px; }
    QTabBar::tab:hover { color: %(text)s; }
    QTabBar::tab:selected { font-weight: 600; }
    QCheckBox, QRadioButton { background: transparent; color: %(text)s; spacing: 6px; }
    QCheckBox:disabled, QRadioButton:disabled { color: %(muted)s; }
    QCheckBox::indicator, QRadioButton::indicator { width: 16px; height: 16px; }
    QTreeWidget { background: %(surface)s; color: %(text)s; border-radius: 4px; padding: 4px; }
    QTreeWidget::item { padding: 4px 3px; border-radius: 3px; }
    QTreeWidget::item:selected { font-weight: 400; background: %(tint)s; color: %(text)s; }
    QTreeWidget::item:focus { border: none; }
    #QuestionPreview { padding: 0; border: 1px solid %(border)s; border-radius: 4px; }
    QScrollBar:vertical { width: 8px; margin: 0; background: %(bg)s; }
    QScrollBar:horizontal { height: 8px; margin: 0; background: %(bg)s; }
    QScrollBar::handle:vertical { min-height: 24px; border-radius: 4px; }
    QScrollBar::handle:horizontal { background: %(border)s; min-width: 24px; border-radius: 4px; }
    QScrollBar::handle:horizontal:hover { background: %(accent)s; }
    QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; border: none; }
    QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
    QToolTip { background: %(surface)s; color: %(text)s; border: 1px solid %(border)s;
        padding: 4px 7px; font-family: "Segoe UI"; font-size: 9pt; }
    """ % colors


if IS_WINDOWS:
    LIGHT_THEME = windows_theme(LIGHT_THEME)
    DARK_THEME = windows_theme(DARK_THEME, dark=True)


class UiIconEngine(QIconEngine):
    """Small vector icons, painted at the actual device scale without font glyphs."""
    def __init__(self, name, accent_surface=False):
        super().__init__()
        self.name = name
        self.accent_surface = accent_surface

    def clone(self):
        return UiIconEngine(self.name, self.accent_surface)

    def pixmap(self, size, mode, state):
        return self.scaledPixmap(size, mode, state, 1.0)

    def scaledPixmap(self, size, mode, state, scale):
        pixmap = QPixmap(round(size.width() * scale), round(size.height() * scale))
        pixmap.setDevicePixelRatio(scale)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        self.paint(painter, QRectF(0, 0, size.width(), size.height()), mode, state)
        painter.end()
        return pixmap

    def paint(self, painter, rect, mode, state):
        palette = QApplication.palette()
        role = QPalette.HighlightedText if self.accent_surface else QPalette.ButtonText
        group = QPalette.Disabled if mode == QIcon.Disabled else QPalette.Active
        color = palette.color(group, role)
        if state == QIcon.On and not self.accent_surface and mode != QIcon.Disabled:
            color = palette.color(QPalette.Highlight)
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        side = min(rect.width(), rect.height())
        painter.translate(rect.center().x() - side / 2, rect.center().y() - side / 2)
        painter.scale(side / 20, side / 20)
        painter.setPen(QPen(color, 1.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(Qt.NoBrush)

        def line(x1, y1, x2, y2):
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        paths = {
            "menu": ((3, 5, 17, 5), (3, 10, 17, 10), (3, 15, 17, 15)),
            "add": ((10, 4, 10, 16), (4, 10, 16, 10)),
            "trash": ((4, 6, 16, 6), (7, 3, 13, 3), (8, 9, 8, 14), (12, 9, 12, 14)),
            "image": ((3, 15, 8, 10), (8, 10, 12, 14), (12, 14, 14, 12), (14, 12, 17, 15)),
            "equation": ((15, 3, 5, 3), (5, 3, 11, 10), (11, 10, 5, 17), (5, 17, 15, 17)),
            "down": ((5, 7, 10, 12), (10, 12, 15, 7)),
            "up": ((5, 12, 10, 7), (10, 7, 15, 12)),
        }
        for coords in paths.get(self.name, ()):
            line(*coords)
        if self.name == "trash":
            path = QPainterPath(QPointF(5, 6))
            path.lineTo(6, 17)
            path.lineTo(14, 17)
            path.lineTo(15, 6)
            painter.drawPath(path)
        elif self.name == "image":
            painter.drawRoundedRect(QRectF(2.5, 3, 15, 14), 1.5, 1.5)
            painter.drawEllipse(QRectF(11.5, 6, 2.5, 2.5))
        elif self.name == "search":
            painter.drawEllipse(QRectF(3, 3, 10, 10))
            line(12, 12, 17, 17)
        elif self.name == "folder":
            path = QPainterPath(QPointF(2, 6))
            for x, y in ((2, 4), (8, 4), (10, 6), (18, 6), (16, 16), (2, 16), (2, 6), (18, 6)):
                path.lineTo(x, y)
            painter.drawPath(path)
        elif self.name in ("bold", "italic", "underline", "strike", "superscript", "subscript"):
            font = interface_font()
            font.setPixelSize(16)
            font.setBold(self.name == "bold")
            font.setItalic(self.name == "italic")
            painter.setFont(font)
            letter = {"bold": "B", "italic": "I", "underline": "U", "strike": "S"}.get(self.name, "x")
            painter.drawText(QRectF(1, 0, 15 if self.name.endswith("script") else 18, 19), Qt.AlignCenter, letter)
            if self.name == "underline":
                line(5, 17, 15, 17)
            elif self.name == "strike":
                line(4, 10, 16, 10)
            elif self.name.endswith("script"):
                font.setPixelSize(10)
                painter.setFont(font)
                painter.drawText(QRectF(12, -2 if self.name == "superscript" else 8, 8, 12), Qt.AlignCenter, "2")
        painter.restore()


def ui_icon(name, accent_surface=False):
    return QIcon(UiIconEngine(name, accent_surface))


def set_ui_icon(button, name):
    if not IS_WINDOWS:
        return
    button.setProperty("uiIcon", name)
    button.setIcon(ui_icon(name, button.objectName() in ("PrimaryButton", "DangerButton")))
    button.setIconSize(QSize(16, 16))
    if isinstance(button, QToolButton):
        button.setAccessibleName(button.toolTip())
        button.setToolButtonStyle(Qt.ToolButtonIconOnly)


def paint_chevron(painter, rect, color, down=True):
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(color, 1.3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    center = QRectF(rect).center()
    direction = 1 if down else -1
    path = QPainterPath(QPointF(center.x() - 3, center.y() - direction * 1.5))
    path.lineTo(center.x(), center.y() + direction * 1.5)
    path.lineTo(center.x() + 3, center.y() - direction * 1.5)
    painter.drawPath(path)
    painter.restore()


class InterfaceComboBox(QComboBox):
    def paintEvent(self, event):
        super().paintEvent(event)
        if IS_WINDOWS:
            option = QStyleOptionComboBox()
            self.initStyleOption(option)
            rect = self.style().subControlRect(QStyle.CC_ComboBox, option, QStyle.SC_ComboBoxArrow, self)
            painter = QPainter(self)
            paint_chevron(painter, rect, self.palette().buttonText().color())
            painter.end()


class InterfaceSpinBox(QSpinBox):
    def paintEvent(self, event):
        super().paintEvent(event)
        if IS_WINDOWS:
            option = QStyleOptionSpinBox()
            self.initStyleOption(option)
            painter = QPainter(self)
            for control, down in ((QStyle.SC_SpinBoxUp, False), (QStyle.SC_SpinBoxDown, True)):
                rect = self.style().subControlRect(QStyle.CC_SpinBox, option, control, self)
                paint_chevron(painter, rect, self.palette().buttonText().color(), down)
            painter.end()


def configure_combo_popup(combo):
    view = QListView()
    view.setFrameShape(QFrame.NoFrame)
    view.setAutoFillBackground(True)
    combo.setView(view)
    popup = view.parentWidget()
    if popup:
        popup.setObjectName("ComboPopupContainer")
        popup.setFrameShape(QFrame.NoFrame)
        popup.setAutoFillBackground(True)

class AddSubjectDialog(QDialog):
    def __init__(self, parent, db_connection):
        super().__init__(parent)
        self.conn = db_connection
        self.setWindowTitle("Adicionar Nova Categoria")
        self.resize(460, 420)
        
        layout = QVBoxLayout(self)
        self.txt_name = QLineEdit()
        layout.addWidget(QLabel("Nome da Categoria:"))
        layout.addWidget(self.txt_name)
        layout.addWidget(QLabel("Adicionar abaixo da categoria selecionada:"))
        self.tree_parent = QTreeWidget()
        self.tree_parent.setHeaderHidden(True)
        self.tree_parent.setMinimumHeight(220)
        self.tree_parent.setSelectionMode(QTreeWidget.SingleSelection)
        layout.addWidget(self.tree_parent, stretch=1)
        
        self.populate_parents()
        
        btn_box = QHBoxLayout()
        btn_save = QPushButton("Salvar")
        btn_save.setObjectName("PrimaryButton")
        btn_save.clicked.connect(self.save_subject)
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        
        btn_box.addStretch()
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

    def show_alert(self, title, text, icon_type=QMessageBox.Information):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.setIcon(icon_type)
        msg_box.addButton("OK", QMessageBox.AcceptRole)
        msg_box.setStyleSheet(self.styleSheet())
        msg_box.exec()

    def populate_parents(self):
        self.tree_parent.clear()
        root_choice = QTreeWidgetItem(self.tree_parent, ["Nenhuma — criar categoria principal"])
        root_choice.setData(0, Qt.UserRole, None)
        self.tree_parent.setCurrentItem(root_choice)
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, nome, parent_id FROM assuntos ORDER BY nome COLLATE NOCASE")
            rows = cursor.fetchall()
            children_by_parent = {}
            for subject_id, name, parent_id in rows:
                children_by_parent.setdefault(parent_id, []).append((subject_id, name))

            def add_children(parent_item, parent_id):
                for subject_id, name in children_by_parent.get(parent_id, []):
                    item = QTreeWidgetItem(parent_item, [name])
                    item.setData(0, Qt.UserRole, subject_id)
                    add_children(item, subject_id)

            for subject_id, name in children_by_parent.get(None, []):
                item = QTreeWidgetItem(self.tree_parent, [name])
                item.setData(0, Qt.UserRole, subject_id)
                add_children(item, subject_id)
        except Exception as e:
            self.show_alert("Erro", f"Não foi possível carregar as categorias: {e}", QMessageBox.Warning)

    def save_subject(self):
        name = self.txt_name.text().strip()
        selected_parent = self.tree_parent.currentItem()
        parent_id = selected_parent.data(0, Qt.UserRole) if selected_parent else None
        
        if not name:
            self.show_alert("Aviso", "O nome não pode estar vazio.", QMessageBox.Warning)
            return
        if ";" in name:
            self.show_alert("Aviso", "O nome não pode conter ponto e vírgula.", QMessageBox.Warning)
            return
            
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO assuntos (nome, parent_id) VALUES (?, ?)", (name, parent_id))
            self.conn.commit()
            self.show_alert("Sucesso", f"Categoria '{name}' cadastrada com sucesso!", QMessageBox.Information)
            self.accept()
        except sqlite3.IntegrityError:
            self.show_alert("Erro", "Esta categoria já existe no sistema.", QMessageBox.Warning)
        except Exception as e:
            self.show_alert("Erro", f"Falha ao salvar:\n{str(e)}", QMessageBox.Critical)


class InsertEquationDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Inserir Fórmula / Equação")
        self.resize(460, 240)
        self.setStyleSheet(parent.styleSheet())

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.cb_type = InterfaceComboBox()
        configure_combo_popup(self.cb_type)
        self.cb_type.setItemDelegate(QStyledItemDelegate())
        self.cb_type.addItems(["Matemática", "Química"])

        self.txt_equation = QTextEdit()
        self.txt_equation.setPlaceholderText("Ex: E = mc^2, x_i, H2O, CO2 -> H2CO3")
        self.txt_equation.setFixedHeight(100)

        form_layout.addRow("Tipo de Equação:", self.cb_type)
        form_layout.addRow("Expressão:", self.txt_equation)
        layout.addLayout(form_layout)

        hint = QLabel("Use ^ para sobrescrito e _ para subscrito. Ex: x^2, CO_2, Fe^{2+}, H2O.")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_insert = QPushButton("Inserir")
        btn_insert.setObjectName("PrimaryButton")
        btn_insert.clicked.connect(self.accept)
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_insert)
        layout.addLayout(btn_box)

    def get_equation_text(self):
        return self.txt_equation.toPlainText().strip()

    def get_equation_type(self):
        return self.cb_type.currentText()


class QuestionCard(QFrame):
    def __init__(self, q_id, subject, difficulty, ano, q_type, html_content, is_selected, toggle_callback,
                 question_source="", source_year="", result_viewport=None,
                 edit_callback=None, duplicate_callback=None, last_modified=None):
        super().__init__()
        self.q_id = q_id
        self._result_viewport = result_viewport
        self._preview_sizing = PreviewSizing()
        self._fitting_preview = False
        if result_viewport is not None:
            result_viewport.installEventFilter(self)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(8)

        header_layout = QHBoxLayout()
        display_subject = (subject or "").replace(";", ", ").strip(", ")
        display_source = (question_source or "").strip() or "Não informada"
        display_source_year = (source_year or "").strip() or "Não informado"
        modified_label = format_last_modified(last_modified) or "Não informada"
        header_label = QLabel(
            f"ID: {q_id} | Segmento/Ano: {ano} | {difficulty} | {q_type}\n"
            f"Assunto: {display_subject}\n"
            f"Fonte da Questão: {display_source} | Ano: {display_source_year}\n"
            f"Última alteração: {modified_label}"
        )
        header_label.setTextFormat(Qt.PlainText)
        header_label.setObjectName("CardLabel")
        header_label.setWordWrap(True)
        
        self.btn_toggle = QPushButton("Ler enunciado" if IS_WINDOWS else "▼ Ler enunciado")
        set_ui_icon(self.btn_toggle, "down")
        self.btn_toggle.setCheckable(True)
        self.btn_toggle.setVisible(False)
        self.btn_toggle.clicked.connect(self.toggle_expansion)
        
        self.checkbox = QCheckBox("Selecionar")
        self.checkbox.setChecked(is_selected)
        self.checkbox.stateChanged.connect(lambda state: toggle_callback(self.q_id, state))
        
        header_layout.addWidget(header_label, stretch=1)
        header_layout.addWidget(self.btn_toggle)
        self.btn_edit = QPushButton("Editar")
        self.btn_edit.clicked.connect(lambda: edit_callback(q_id) if edit_callback else None)
        header_layout.addWidget(self.btn_edit)
        self.btn_duplicate = QPushButton("Duplicar")
        self.btn_duplicate.clicked.connect(lambda: duplicate_callback(q_id) if duplicate_callback else None)
        header_layout.addWidget(self.btn_duplicate)
        header_layout.addWidget(self.checkbox)
        self.layout.addLayout(header_layout)

        self.view_panel = QTextEdit()
        self.view_panel.setObjectName("QuestionPreview")
        self.view_panel.setHtml(html_content)
        font_format = QTextCharFormat()
        font_format.setFontFamilies(["Segoe UI" if IS_WINDOWS else "Arial"])
        font_format.setFontPointSize(11 if IS_WINDOWS else 16)
        text_cursor = self.view_panel.textCursor()
        text_cursor.select(QTextCursor.Document)
        text_cursor.mergeCharFormat(font_format)
        text_cursor.clearSelection()
        text_cursor.movePosition(QTextCursor.Start)
        self.view_panel.setTextCursor(text_cursor)
        self.view_panel.setReadOnly(True)
        self.view_panel.setLineWrapMode(QTextEdit.WidgetWidth)
        self.view_panel.setStyleSheet("background-color: transparent; padding: 0px;")
        self.view_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        self.view_panel.setMinimumHeight(0)
        self.view_panel.setMaximumHeight(150)
        self.view_panel._resize_minimum = 60
        self.view_panel._preview_card = self
        self._preview_content_height = 0
        self.layout.addWidget(self.view_panel)
        self.view_panel.document().documentLayout().documentSizeChanged.connect(self._fit_initial_preview)
        QTimer.singleShot(0, self, self._fit_initial_preview)
        self.resize_handle = VerticalResizeHandle(self.view_panel)
        self.layout.addWidget(self.resize_handle, alignment=Qt.AlignRight)

    def _preview_geometry(self):
        viewport = self._result_viewport
        viewport_height = viewport.height() if viewport is not None else self.window().height()
        if viewport_height <= 0:
            viewport_height = 600
        margins = self.layout.contentsMargins()
        header = self.layout.itemAt(0).sizeHint().height()
        chrome = margins.top() + margins.bottom() + header + self.resize_handle.height() + 2 * self.layout.spacing()
        return viewport_height, chrome

    def _set_preview_height(self, height):
        if self.view_panel.height() != height:
            self.view_panel.setFixedHeight(height)

    def _fit_initial_preview(self, *_):
        if self._fitting_preview:
            return
        self._fitting_preview = True
        try:
            viewport_width = self.view_panel.viewport().width()
            if viewport_width <= 0:
                return
            document = self.view_panel.document()
            if document.textWidth() != viewport_width:
                document.setTextWidth(viewport_width)
            content_height = document.documentLayout().documentSize().height()
            if content_height <= 0:
                return
            self._preview_content_height = max(1, int(content_height + 12))
            self.btn_toggle.setVisible(self._preview_content_height > 150)
            self._set_preview_height(self._preview_sizing.fit(self._preview_content_height, *self._preview_geometry()))
        finally:
            self._fitting_preview = False

    def eventFilter(self, watched, event):
        if watched is self._result_viewport and event.type() == QEvent.Resize:
            QTimer.singleShot(0, self, self._fit_initial_preview)
        return super().eventFilter(watched, event)

    def begin_preview_drag(self, pointer_y):
        self._preview_sizing.begin_drag(self.view_panel.height(), pointer_y)

    def move_preview_drag(self, pointer_y):
        self._set_preview_height(self._preview_sizing.drag_to(pointer_y, *self._preview_geometry()))

    def end_preview_drag(self):
        self._preview_sizing.end_drag()

    def toggle_expansion(self):
        expanded = self.btn_toggle.isChecked()
        self._preview_sizing.toggle(expanded)
        self._fit_initial_preview()
        self.btn_toggle.setText(("Ocultar" if IS_WINDOWS else "▲ Ocultar") if expanded else
                                ("Ler enunciado" if IS_WINDOWS else "▼ Ler enunciado"))
        set_ui_icon(self.btn_toggle, "up" if expanded else "down")


class VerticalResizeHandle(QWidget):
    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self._start_y = None
        self.setObjectName("ResizeHandle")
        self.setFixedSize(16, 16)
        self.setCursor(Qt.SizeVerCursor)
        self.setFocusPolicy(Qt.NoFocus)
        self.setToolTip("Arraste para ajustar a altura")

    def paintEvent(self, event):
        painter = QPainter(self)
        pen = QPen(self.palette().mid().color(), 1.2)
        painter.setPen(pen)
        for offset in (0, 4, 8):
            painter.drawLine(self.width() - 5 - offset, self.height() - 1,
                             self.width() - 1, self.height() - 5 - offset)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._start_y = event.globalPosition().toPoint().y()
            if hasattr(self.owner, "_preview_card"):
                self.owner._preview_card.begin_preview_drag(self._start_y)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._start_y is not None:
            current_y = event.globalPosition().toPoint().y()
            if not event.buttons() & Qt.LeftButton:
                self._end_drag()
                return
            if hasattr(self.owner, "_preview_card"):
                self.owner._preview_card.move_preview_drag(current_y)
            else:
                delta = current_y - self._start_y
                self.owner.setFixedHeight(legacy_drag_height(self.owner.height(), delta, self.owner._resize_minimum))
                self._start_y = current_y
            event.accept()
            return
        super().mouseMoveEvent(event)

    def _end_drag(self):
        if self._start_y is not None and hasattr(self.owner, "_preview_card"):
            self.owner._preview_card.end_preview_drag()
        self._start_y = None

    def event(self, event):
        if event.type() in (QEvent.UngrabMouse, QEvent.Hide):
            self._end_drag()
        return super().event(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._end_drag()
            event.accept()
            return
        super().mouseReleaseEvent(event)


class VerticalResizeMixin:
    """Adds a bottom-center grip that changes a widget's height only."""
    def setup_vertical_resize(self, initial_height, minimum_height):
        self._resize_minimum = minimum_height
        self.setMinimumHeight(minimum_height)
        self.setFixedHeight(initial_height)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._resize_handle = VerticalResizeHandle(self)
        self._position_resize_handle()

    def _position_resize_handle(self):
        if hasattr(self, "_resize_handle"):
            handle = self._resize_handle
            handle.move(self.width() - handle.width() - 2, self.height() - handle.height() - 2)
            handle.raise_()


class ResizableTextEdit(VerticalResizeMixin, QTextEdit):
    def __init__(self, initial_height=110, minimum_height=64, parent=None):
        super().__init__(parent)
        if IS_WINDOWS:
            self.document().setDefaultFont(interface_font())
        self.setup_vertical_resize(initial_height, minimum_height)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_resize_handle()


class ClipboardRichTextEdit(ResizableTextEdit):
    def insertFromMimeData(self, source):
        if source.hasHtml():
            fallback = None
            if source.hasImage():
                try:
                    fallback = clipboard_image_data(source.imageData())
                except ImageReadError:
                    QMessageBox.warning(self, "Imagem não incorporada", "Não foi possível ler a imagem copiada.")
            prepared, issues = embed_html_images(source.html(), fallback_image=fallback)
            if issues:
                QMessageBox.warning(self, "Imagens não incorporadas", "Não foi possível incorporar as seguintes imagens:\n" + "\n".join(item[:200] or "(sem endereço)" for item in issues))
            safe_source = QMimeData()
            safe_source.setHtml(prepared)
            super().insertFromMimeData(safe_source)
            return
        if source.hasImage() and not source.hasHtml():
            image = QImage(source.imageData())
            if not image.isNull():
                if image.width() > 500:
                    image = image.scaledToWidth(500, Qt.SmoothTransformation)
                byte_array = QByteArray()
                buffer = QBuffer(byte_array)
                buffer.open(QIODevice.WriteOnly)
                image.save(buffer, "PNG")
                buffer.close()
                image_format = QTextImageFormat()
                image_format.setName("data:image/png;base64," + byte_array.toBase64().data().decode("ascii"))
                image_format.setWidth(image.width())
                image_format.setHeight(image.height())
                self.textCursor().insertImage(image_format)
                return
            QMessageBox.warning(self, "Imagem não incorporada", "Não foi possível ler a imagem copiada.")
            return
        super().insertFromMimeData(source)


class AccessibleSelectionStyle(QProxyStyle):
    def drawPrimitive(self, element, option, painter, widget=None):
        if element == QStyle.PE_IndicatorBranch:
            if not option.state & QStyle.State_Children:
                return
            rect = option.rect
            center_x = rect.center().x()
            center_y = rect.center().y()
            if option.state & QStyle.State_Open:
                points = QPolygon([
                    QPoint(center_x - 4, center_y - 2),
                    QPoint(center_x + 4, center_y - 2),
                    QPoint(center_x, center_y + 3),
                ])
            else:
                points = QPolygon([
                    QPoint(center_x - 2, center_y - 4),
                    QPoint(center_x - 2, center_y + 4),
                    QPoint(center_x + 3, center_y),
                ])
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(Qt.NoPen)
            painter.setBrush(option.palette.text())
            painter.drawPolygon(points)
            painter.restore()
            return

        checkbox_primitives = (QStyle.PE_IndicatorCheckBox, QStyle.PE_IndicatorItemViewItemCheck)
        if element in checkbox_primitives:
            text_color = option.palette.text().color()
            dark_surface = text_color.lightness() > 150
            accent = QColor("#10B981" if dark_surface else "#059669")
            mark = QColor("#11111B" if dark_surface else "#FFFFFF")
            surface = QColor("#313244" if dark_surface else "#FFFFFF")
            border = QColor("#64748B" if dark_surface else "#94A3B8")
            if not option.state & QStyle.State_Enabled:
                surface = QColor("#252538" if dark_surface else "#F1F5F9")
                border = QColor("#45475A" if dark_surface else "#CBD5E1")
                accent = QColor("#53685F" if dark_surface else "#A7DCC7")
                mark = QColor("#313244" if dark_surface else "#F8FAFC")
            rect = option.rect.adjusted(1, 1, -1, -1)
            checked = bool(option.state & QStyle.State_On)
            partial = bool(option.state & QStyle.State_NoChange)

            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(QPen(accent if checked else border, 1.2))
            painter.setBrush(accent if checked else surface)
            painter.drawRoundedRect(rect, 3, 3)
            if checked:
                painter.setPen(QPen(mark, 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                path = QPainterPath()
                path.moveTo(rect.left() + rect.width() * 0.23, rect.center().y())
                path.lineTo(rect.left() + rect.width() * 0.43, rect.center().y() + rect.height() * 0.2)
                path.lineTo(rect.left() + rect.width() * 0.77, rect.top() + rect.height() * 0.28)
                painter.drawPath(path)
            elif partial:
                painter.setPen(QPen(border, 1.8, Qt.SolidLine, Qt.RoundCap))
                painter.drawLine(rect.left() + 3, rect.center().y(), rect.right() - 3, rect.center().y())
            painter.restore()
            return

        if element == QStyle.PE_IndicatorRadioButton:
            text_color = option.palette.text().color()
            dark_surface = text_color.lightness() > 150
            accent = QColor("#10B981" if dark_surface else "#059669")
            mark = QColor("#11111B" if dark_surface else "#FFFFFF")
            surface = QColor("#313244" if dark_surface else "#FFFFFF")
            border = QColor("#64748B" if dark_surface else "#94A3B8")
            if not option.state & QStyle.State_Enabled:
                surface = QColor("#252538" if dark_surface else "#F1F5F9")
                border = QColor("#45475A" if dark_surface else "#CBD5E1")
                accent = QColor("#53685F" if dark_surface else "#A7DCC7")
            rect = option.rect.adjusted(2, 2, -2, -2)
            checked = bool(option.state & QStyle.State_On)

            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(QPen(accent if checked else border, 1.3))
            painter.setBrush(accent if checked else surface)
            painter.drawEllipse(rect)
            if checked:
                painter.setPen(Qt.NoPen)
                painter.setBrush(mark)
                painter.drawEllipse(rect.adjusted(4, 4, -4, -4))
            painter.restore()
            return

        return super().drawPrimitive(element, option, painter, widget)


class ResizableTreeWidget(VerticalResizeMixin, QTreeWidget):
    def __init__(self, initial_height=220, minimum_height=120, parent=None):
        super().__init__(parent)
        self.setup_vertical_resize(initial_height, minimum_height)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_resize_handle()

def dispose_question_card(widget):
    """Disconnect preview callbacks before Qt deletes a result card."""
    if isinstance(widget, QuestionCard):
        widget.view_panel.document().documentLayout().documentSizeChanged.disconnect(widget._fit_initial_preview)
    widget.deleteLater()


class ExamGeneratorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        QApplication.setFont(interface_font())
        if IS_WINDOWS:
            # One base style also covers controls created later and modal dialogs.
            QApplication.instance().setStyle(AccessibleSelectionStyle(QStyleFactory.create("Fusion")))
        self.resize(1250, 850)
        self.is_dark_mode = False
        self.apply_theme()
        self._selection_style = QApplication.style() if IS_WINDOWS else AccessibleSelectionStyle(QStyleFactory.create("Fusion"))
        self.conn = None
        self.search_view = SearchViewState()
        self.exam_order = ExamOrder()
        self.selected_ids = self.search_view.selected_ids
        self.question_session = None
        first_run = not os.path.exists(os.path.join(self.get_data_dir(), "app_config.json"))
        self.config_data = self.load_global_config()
        self.current_discipline = self.config_data["current_discipline"]
        self.db_path = self.config_data["disciplines"].get(self.current_discipline, "")
        self.setup_ui()
        self._active_editor = self.txt_prompt
        for editor in (self.txt_prompt, *self.alt_inputs.values(), self.txt_essay_answer):
            editor.installEventFilter(self)
            if editor is not self.txt_prompt:
                editor.cursorPositionChanged.connect(self.update_toolbar_states)
        self.form_snapshot = self.question_draft_from_form()
        create_default = False
        if first_run and self.db_path and not os.path.exists(self.db_path):
            create_default = self.show_confirm(
                "Criar banco padrão", f"Criar o banco padrão de Biologia em:\n{self.db_path}?")
        if self.db_path and (not first_run or os.path.exists(self.db_path) or create_default):
            self.switch_database_connection(create=create_default)

    def apply_theme(self):
        if IS_WINDOWS:
            palette = QPalette()
            dark = self.is_dark_mode
            for role, light, dim in (
                (QPalette.Window, "#F8FAFC", "#1E1E2E"),
                (QPalette.Base, "#FFFFFF", "#292A3D"),
                (QPalette.AlternateBase, "#F1F5F9", "#252538"),
                (QPalette.Button, "#FFFFFF", "#292A3D"),
                (QPalette.WindowText, "#334155", "#E2E8F0"),
                (QPalette.Text, "#334155", "#E2E8F0"),
                (QPalette.ButtonText, "#334155", "#E2E8F0"),
                (QPalette.PlaceholderText, "#64748B", "#A6ADC8"),
                (QPalette.Highlight, "#059669", "#10B981"),
                (QPalette.HighlightedText, "#FFFFFF", "#11111B"),
                (QPalette.ToolTipBase, "#FFFFFF", "#292A3D"),
                (QPalette.ToolTipText, "#334155", "#E2E8F0"),
            ):
                palette.setColor(role, QColor(dim if dark else light))
            for role in (QPalette.Text, QPalette.WindowText, QPalette.ButtonText):
                palette.setColor(QPalette.Disabled, role, QColor("#A6ADC8" if dark else "#64748B"))
            QApplication.instance().setPalette(palette)
        self.setStyleSheet(DARK_THEME if self.is_dark_mode else LIGHT_THEME)
        # Refresh icon caches after a palette change (including existing cards).
        if IS_WINDOWS:
            for button in self.findChildren(QPushButton) + self.findChildren(QToolButton):
                if button.property("uiIcon"):
                    set_ui_icon(button, button.property("uiIcon"))

    def get_data_dir(self):
        return storage_config.data_dir()

    def load_global_config(self):
        return storage_config.load_config(self.get_data_dir())

    def save_global_config(self, candidate, created_path=None):
        try:
            storage_config.save_config(candidate, self.get_data_dir())
        except OSError as e:
            message = f"Não foi possível salvar a configuração: {e}"
            if created_path:
                message += f"\n\nO banco criado foi mantido em:\n{created_path}"
            self.show_alert("Erro", message, QMessageBox.Critical)
            return False
        self.config_data = candidate
        return True

    def switch_database_connection(self, create=False, candidate=None):
        """Open the requested bank before releasing the previous connection."""
        if not self.db_path:
            self.show_alert("Erro", "O caminho do banco de dados não está configurado.", QMessageBox.Warning)
            return False
        new_conn = None
        try:
            new_conn = storage_database.open_bank(
                self.db_path, create=create, backup_dir=self.get_data_dir(),
                confirm_delete=lambda path: self.show_confirm(
                    "Excluir backup antigo", f"Para continuar a atualização, excluir o backup antigo?\n\n{path}"))
            storage_database.seed_biology_categories(new_conn, self.current_discipline)
        except storage_backup.BackupCancelled:
            return False
        except storage_database.BankNotFoundError:
            return self.handle_missing_bank(candidate)
        except storage_database.NotABankError:
            self.show_alert("Banco inválido", f"O arquivo não é um banco de questões válido:\n{self.db_path}", QMessageBox.Warning)
            return False
        except storage_database.BankTooNewError:
            self.show_alert("Atualização necessária", "Este banco foi criado por uma versão mais nova do Prometheus. Atualize o aplicativo para abri-lo.", QMessageBox.Warning)
            return False
        except Exception as e:
            if new_conn:
                new_conn.close()
            self.show_alert("Erro", f"Não foi possível abrir o banco de dados:\n{self.db_path}\n\n{e}", QMessageBox.Warning)
            return False
        if candidate is not None and not self.save_global_config(candidate, self.db_path if create else None):
            new_conn.close()
            return False
        old_conn, self.conn = self.conn, new_conn
        if old_conn:
            try:
                old_conn.close()
            except Exception as e:
                self.show_alert("Aviso", f"Não foi possível fechar o banco anterior: {e}", QMessageBox.Warning)
        database_name = os.path.splitext(os.path.basename(self.db_path))[0] or self.current_discipline
        self.setWindowTitle(f"{APP_NAME} — {database_name}")
        self.selected_ids.clear()
        self.exam_order.synchronize(self.selected_ids)
        self.search_view.set_selected_only(False)
        if hasattr(self, "lbl_selected_count"):
            self.lbl_selected_count.setText("0 questão(ões) selecionada(s) para a prova")
            self.btn_delete_selected_questions.setEnabled(False)
            self.btn_browse_selected_questions.blockSignals(True)
            self.btn_browse_selected_questions.setChecked(False)
            self.btn_browse_selected_questions.setText("Navegar pelas questões selecionadas")
            self.btn_browse_selected_questions.setEnabled(False)
            self.btn_browse_selected_questions.blockSignals(False)
            self.update_multi_version_controls()
        self.reset_question_form()
        self.reload_all_trees()
        applied = self.search_view.applied
        self.search_view.apply(self.current_search_filters((applied.source_year_from, applied.source_year_to)))
        self.load_questions()
        return True

    def handle_missing_bank(self, pending_config=None):
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Banco não encontrado")
        dialog.setText(f"O banco da disciplina '{self.current_discipline}' não foi encontrado:\n{self.db_path}")
        locate = dialog.addButton("Localizar arquivo", QMessageBox.ActionRole)
        remove = dialog.addButton("Remover da lista", QMessageBox.ActionRole)
        dialog.addButton("Cancelar", QMessageBox.RejectRole)
        dialog.exec()
        if dialog.clickedButton() == locate:
            path, _ = QFileDialog.getOpenFileName(self, "Localizar banco", "", "SQLite Database (*.db)")
            if not path:
                return False
            previous = self.db_path
            self.db_path = path
            candidate = storage_config.copy_config(pending_config if pending_config is not None else self.config_data)
            storage_config.relink_discipline(candidate, self.current_discipline, path)
            candidate['current_discipline'] = self.current_discipline
            if self.switch_database_connection(candidate=candidate):
                self.txt_db_path.setText(path)
                return True
            self.db_path = previous
        elif dialog.clickedButton() == remove:
            if not self.show_confirm("Remover disciplina", f"Remover '{self.current_discipline}' da lista? O arquivo será mantido no disco."):
                return False
            candidate = storage_config.copy_config(self.config_data)
            storage_config.remove_discipline(candidate, self.current_discipline)
            if not self.save_global_config(candidate):
                return False
            if self.conn is None:
                self.current_discipline = self.config_data['current_discipline']
                self.db_path = self.config_data['disciplines'].get(self.current_discipline, '')
                self.refresh_disciplines_dropdown()
                self.txt_db_path.setText(self.db_path)
                if self.db_path:
                    return self.switch_database_connection()
        return False

    # --- POP-UP RE-ARCHITECTURE ENGINES ---
    def show_alert(self, title, text, icon_type=QMessageBox.Information):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.setIcon(icon_type)
        msg_box.addButton("OK", QMessageBox.AcceptRole)
        msg_box.setStyleSheet(self.styleSheet())
        msg_box.exec()

    def show_help(self):
        help_text = """
        <h2>Guia rápido</h2>
        <h3>Backups e bancos não encontrados</h3>
        <p>Use <b>Fazer backup</b> no menu para salvar uma cópia do banco em outro local. Antes de atualizar a estrutura de um banco, o Prometheus faz uma cópia automática. Se for necessário excluir um backup antigo, o aplicativo pedirá confirmação.</p>
        <p>Se um banco tiver sido movido ou estiver indisponível, use <b>Localizar arquivo</b> para apontar para ele, ou <b>Remover da lista</b> para remover apenas a disciplina. O arquivo não é apagado.</p>
        <h3>1. Cadastrar Questão</h3>
        <p>Escolha o tipo e a dificuldade, informe o segmento e os anos/séries, selecione as categorias e preencha o enunciado. Nas questões de múltipla escolha, escreva as alternativas e marque a correta. Nas dissertativas, você pode registrar a resolução esperada. Clique em <b>Salvar Questão</b> para adicionar ao banco. A barra de formatação e o botão de equação atuam no último campo de texto selecionado, inclusive alternativas e resposta esperada.</p>
        <p>Na busca, use <b>Editar</b> para alterar uma questão mantendo seu ID, ou <b>Duplicar</b> para criar outra. A opção <b>Cancelar edição</b> retorna ao cadastro; alterações não salvas exigem confirmação antes de serem descartadas. Os cartões mostram a última alteração quando essa informação estiver disponível.</p>
        <h3>2. Buscar e Selecionar Questões</h3>
        <p>Use os filtros de categoria, texto, fonte da questão, ano da fonte, dificuldade, ano/série escolar e tipo; depois clique em <b>Filtrar Questões</b>. A fonte pode ser buscada por parte do nome. Para o ano da fonte, use <b>Desde</b> para incluir esse ano e os seguintes, <b>até</b> para incluir esse ano e os anteriores, ou ambos para limitar o intervalo. Por exemplo: Desde 2022; até 2024; ou Desde 2022 até 2024. Use o mesmo ano nos dois campos para buscar um ano numérico exato. Deixe os campos vazios para buscar sem essas restrições. Abra os cartões para revisar enunciados, alternativas e respostas. Marque <b>Selecionar</b> nas questões que entrarão na prova. Os resultados aparecem em páginas de até 50 questões; use <b>Anterior</b>, <b>Próxima</b> ou o número da página para navegar. A seleção permanece ao trocar de página ou filtro. Use <b>Navegar pelas questões selecionadas</b> para ver apenas essas questões. A exclusão de questões selecionadas inclui também as seleções que não estão visíveis na página atual.</p>
        <h3>3. Configurar e Gerar Prova</h3>
        <p>Depois de selecionar questões, use <b>Subir</b> e <b>Descer</b> para definir a ordem. Escolha se deseja incluir o gabarito ao final ou em arquivo separado. Para versões diferentes, ative <b>Gerar múltiplas versões</b> e escolha o embaralhamento. Questões marcadas para manter a ordem não têm suas alternativas embaralhadas. As versões recebem números e arquivos com <b>_Versao_</b> no nome. Se alguma imagem não puder ser exportada, o aplicativo informa a questão antes de salvar. Os arquivos não incluem cabeçalho escolar: copie as questões para o modelo da escola.</p>
        """
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Ajuda")
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setText(help_text)
        msg_box.setMinimumWidth(620)
        msg_box.addButton("Fechar", QMessageBox.AcceptRole)
        msg_box.setStyleSheet(self.styleSheet())
        msg_box.exec()

    def show_about(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Sobre o Prometheus")
        dialog.setMinimumWidth(520)
        layout = QVBoxLayout(dialog)

        about_text = QLabel(
            f"{APP_NAME} {__version__} foi desenvolvido por Pedro Trevisan "
            "sozinho, com a ajuda de ferramentas de inteligência artificial. Erros e bugs "
            "podem ter passado despercebidos. Como não se trata de um programa com "
            "desenvolvimento constante, atualizações e correções acontecerão apenas em "
            "casos de bugs severos.\n\n"
            "Se quiser agradecer o desenvolvimento e distribuição do programa, faça uma "
            "doação! Qualquer valor é bem-vindo!"
        )
        about_text.setWordWrap(True)
        layout.addWidget(about_text)

        donate_button = QPushButton("Doação - Pix via QR Code")
        donate_button.setObjectName("PrimaryButton")
        donate_button.clicked.connect(self.show_pix_qr)
        layout.addWidget(donate_button)

        dialog.setStyleSheet(
            self.styleSheet()
            + (
                "QDialog { background-color: #1E1E2E; color: #E2E8F0; }"
                "QDialog QLabel { background-color: transparent; color: #E2E8F0; }"
                if self.is_dark_mode else
                "QDialog { background-color: #F8FAFC; color: #334155; }"
                "QDialog QLabel { background-color: transparent; color: #334155; }"
            )
        )
        dialog.exec()

    def show_pix_qr(self):
        pixmap = QPixmap()
        pixmap.load(str(asset_path("pix_qr.jpg")), "JPEG")
        if pixmap.isNull():
            self.show_alert(
                "QR Code Pix",
                "Não foi possível carregar o QR Code Pix.",
                QMessageBox.Warning,
            )
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Doação - Pix")
        layout = QVBoxLayout(dialog)
        image = QLabel()
        image.setAlignment(Qt.AlignCenter)
        image.setPixmap(pixmap.scaled(474, 474, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(image)
        close_button = QPushButton("Fechar")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button, alignment=Qt.AlignRight)
        dialog.setStyleSheet(self.styleSheet())
        dialog.exec()

    def show_confirm(self, title, text):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.setIcon(QMessageBox.Question)
        yes_btn = msg_box.addButton("Sim", QMessageBox.YesRole)
        no_btn = msg_box.addButton("Não", QMessageBox.NoRole)
        msg_box.setStyleSheet(self.styleSheet())
        msg_box.exec()
        return msg_box.clickedButton() == yes_btn

    def get_text_prompt(self, title, label):
        dialog = QInputDialog(self)
        dialog.setWindowTitle(title)
        dialog.setLabelText(label)
        dialog.setStyleSheet(self.styleSheet())
        if dialog.exec() == QDialog.Accepted:
            return dialog.textValue()
        return None

    # --- MAIN UI SETUP ---
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Alterado para self.sidebar para podermos ocultar depois
        self.sidebar = QFrame()
        self.sidebar.setObjectName("SettingsPanel")
        self.sidebar.setFixedWidth(280)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(18, 20, 18, 20)
        sidebar_layout.setSpacing(12)

        lbl_settings_title = QLabel("Disciplinas e Bancos")
        lbl_settings_title.setObjectName("FilterHeaderLabel")
        lbl_settings_title.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(lbl_settings_title)

        sidebar_layout.addWidget(QLabel("Disciplina Atual:"))
        self.cb_disciplines = InterfaceComboBox()
        configure_combo_popup(self.cb_disciplines)
        self.cb_disciplines.setItemDelegate(QStyledItemDelegate())
        self.refresh_disciplines_dropdown()
        self.cb_disciplines.currentTextChanged.connect(self.on_discipline_changed)
        sidebar_layout.addWidget(self.cb_disciplines)

        lbl_db_path = QLabel("Arquivo do Banco de Dados:")
        self.txt_db_path = QLineEdit()
        self.txt_db_path.setText(self.db_path)
        self.txt_db_path.setReadOnly(True)
        sidebar_layout.addWidget(lbl_db_path)
        sidebar_layout.addWidget(self.txt_db_path)

        btn_new_db = QPushButton("Criar Novo Banco\n(Disciplina)" if IS_WINDOWS else "➕ Criar Novo Banco\n(Disciplina)")
        set_ui_icon(btn_new_db, "add")
        btn_new_db.setMinimumHeight(48 if IS_WINDOWS else 64)
        btn_new_db.clicked.connect(self.action_create_new_database)
        sidebar_layout.addWidget(btn_new_db)

        btn_link_db = QPushButton("Abrir Banco Existente (.db)" if IS_WINDOWS else "🔗 Abrir Banco Existente (.db)")
        set_ui_icon(btn_link_db, "folder")
        btn_link_db.clicked.connect(self.action_link_existing_database)
        sidebar_layout.addWidget(btn_link_db)

        btn_backup = QPushButton("Fazer backup")
        btn_backup.clicked.connect(self.action_backup_database)
        sidebar_layout.addWidget(btn_backup)

        btn_rename = QPushButton("Renomear disciplina")
        btn_rename.clicked.connect(self.action_rename_discipline)
        sidebar_layout.addWidget(btn_rename)
        btn_remove = QPushButton("Remover da lista")
        btn_remove.clicked.connect(self.action_remove_discipline)
        sidebar_layout.addWidget(btn_remove)

        sidebar_divider = QFrame()
        sidebar_divider.setObjectName("FilterSectionDivider")
        sidebar_divider.setFixedHeight(3)
        sidebar_layout.addSpacing(4)
        sidebar_layout.addWidget(sidebar_divider)

        theme_header = QLabel("Tema Visual")
        theme_header.setObjectName("FilterHeaderLabel")
        theme_header.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(theme_header)
        self.btn_toggle_theme = QPushButton("Alternar para Modo Escuro")
        self.btn_toggle_theme.clicked.connect(self.toggle_theme)
        sidebar_layout.addWidget(self.btn_toggle_theme)
        
        sidebar_layout.addStretch()

        utility_divider = QFrame()
        utility_divider.setObjectName("FilterSectionDivider")
        utility_divider.setFixedHeight(3)
        sidebar_layout.addWidget(utility_divider)

        self.btn_help = QPushButton("Ajuda")
        self.btn_help.setObjectName("SidebarUtilityButton")
        self.btn_help.setFixedHeight(30 if IS_WINDOWS else 38)
        self.btn_help.clicked.connect(self.show_help)
        sidebar_layout.addWidget(self.btn_help)

        self.btn_about = QPushButton("Sobre")
        self.btn_about.setObjectName("SidebarUtilityButton")
        self.btn_about.setFixedHeight(30 if IS_WINDOWS else 38)
        self.btn_about.clicked.connect(self.show_about)
        sidebar_layout.addWidget(self.btn_about)

        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(20, 20, 20, 20)

        # NOVO: Barra superior com botão para recolher a barra lateral
        top_bar_layout = QHBoxLayout()
        self.btn_toggle_sidebar = QPushButton("Menu" if IS_WINDOWS else "☰ Menu")
        set_ui_icon(self.btn_toggle_sidebar, "menu")
        self.btn_toggle_sidebar.setFixedWidth(100)
        self.btn_toggle_sidebar.clicked.connect(self.toggle_sidebar)
        top_bar_layout.addWidget(self.btn_toggle_sidebar)
        top_bar_layout.addStretch() # Empurra o botão para a esquerda
        
        content_layout.addLayout(top_bar_layout)

        self.tabs = QTabWidget()
        self.setup_tab_register()
        self.setup_tab_search()
        self.setup_tab_generate()
        self.tabs.currentChanged.connect(self.on_exam_tab_changed)

        content_layout.addWidget(self.tabs)
        
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(content_area)
        selection_widgets = (
            self.findChildren(QCheckBox)
            + self.findChildren(QRadioButton)
            + self.findChildren(QTreeWidget)
        )
        for widget in selection_widgets:
            widget.setStyle(self._selection_style)
        self.sidebar.hide()

    # NOVA FUNÇÃO: Alterna a visibilidade da barra lateral
    def toggle_sidebar(self):
        if self.sidebar.isVisible():
            self.sidebar.setVisible(False)
        else:
            self.sidebar.setVisible(True)
            
    # --- MULTI-DISCIPLINE LOGIC ---
    def refresh_disciplines_dropdown(self):
        self.cb_disciplines.blockSignals(True)
        self.cb_disciplines.clear()
        self.cb_disciplines.addItems(list(self.config_data["disciplines"].keys()))
        self.cb_disciplines.setCurrentText(self.current_discipline)
        self.cb_disciplines.blockSignals(False)

    def on_discipline_changed(self, new_discipline):
        if not new_discipline or new_discipline == self.current_discipline:
            return
        if new_discipline not in self.config_data['disciplines']:
            self.refresh_disciplines_dropdown()
            return
        if not self.confirm_discard_question():
            self.refresh_disciplines_dropdown()
            return
        old_name, old_path = self.current_discipline, self.db_path
        self.current_discipline = new_discipline
        self.db_path = self.config_data["disciplines"][new_discipline]
        candidate = storage_config.copy_config(self.config_data)
        candidate['current_discipline'] = new_discipline
        if not self.switch_database_connection(candidate=candidate):
            self.current_discipline, self.db_path = old_name, old_path
            self.refresh_disciplines_dropdown()
            return
        self.txt_db_path.setText(self.db_path)

    def action_create_new_database(self):
        if not self.confirm_discard_question():
            return
        disc_name = self.get_text_prompt("Nova Disciplina", "Digite o nome da nova Disciplina (ex: Matemática, História):")
        if not disc_name: return
        disc_name = disc_name.strip()
        try:
            storage_config.add_discipline({'disciplines': self.config_data['disciplines'].copy()}, disc_name, '')
        except ValueError:
            self.show_alert("Aviso", "Nome vazio ou já existente. Escolha outro nome.", QMessageBox.Warning)
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Salvar Banco de Dados", f"banco_{disc_name.lower().replace(' ', '_')}.db",
            "SQLite Database (*.db)")
        if not file_path: return
        self.warn_cloud_bank(file_path)
        old_name, old_path = self.current_discipline, self.db_path
        self.current_discipline, self.db_path = disc_name, file_path
        candidate = storage_config.copy_config(self.config_data)
        storage_config.add_discipline(candidate, disc_name, file_path)
        candidate['current_discipline'] = disc_name
        if not self.switch_database_connection(create=True, candidate=candidate):
            self.current_discipline, self.db_path = old_name, old_path
            return
        self.txt_db_path.setText(file_path)
        self.refresh_disciplines_dropdown()
        self.show_alert("Sucesso", f"Disciplina '{disc_name}' criada com sucesso!", QMessageBox.Information)

    def action_link_existing_database(self):
        if not self.confirm_discard_question():
            return
        file_path, _ = QFileDialog.getOpenFileName(self, "Abrir Banco de Dados (.db)", "", "SQLite Database (*.db)")
        if not file_path: return
        disc_name = self.get_text_prompt("Vincular Banco", "Digite um nome para identificar esta Disciplina no menu:")
        if not disc_name: return
        disc_name = disc_name.strip()
        try:
            storage_config.add_discipline({'disciplines': self.config_data['disciplines'].copy()}, disc_name, '')
        except ValueError:
            self.show_alert("Aviso", "Nome vazio ou já existente. Escolha outro nome.", QMessageBox.Warning)
            return
        self.warn_cloud_bank(file_path)
        old_name, old_path = self.current_discipline, self.db_path
        self.current_discipline, self.db_path = disc_name, file_path
        candidate = storage_config.copy_config(self.config_data)
        storage_config.add_discipline(candidate, disc_name, file_path)
        candidate['current_discipline'] = disc_name
        if not self.switch_database_connection(candidate=candidate):
            self.current_discipline, self.db_path = old_name, old_path
            return
        self.txt_db_path.setText(file_path)
        self.refresh_disciplines_dropdown()
        self.show_alert("Sucesso", f"Banco vinculado à disciplina '{disc_name}' com sucesso!", QMessageBox.Information)

    def warn_cloud_bank(self, path):
        if storage_backup.is_cloud_path(path):
            self.show_alert("Banco em pasta sincronizada", "Sincronizar um banco aberto pode danificá-lo. Mantenha backups e prefira uma pasta local.", QMessageBox.Warning)

    def action_rename_discipline(self):
        if not self.current_discipline:
            self.show_alert("Aviso", "Não há disciplina selecionada.", QMessageBox.Warning)
            return
        name = self.get_text_prompt("Renomear disciplina", "Digite o novo nome da disciplina:")
        if name is None:
            return
        candidate = storage_config.copy_config(self.config_data)
        try:
            renamed = storage_config.rename_discipline(candidate, self.current_discipline, name)
        except ValueError:
            self.show_alert("Aviso", "Nome vazio ou já existente. Escolha outro nome.", QMessageBox.Warning)
            return
        if not self.save_global_config(candidate):
            return
        self.current_discipline = renamed
        self.refresh_disciplines_dropdown()

    def action_remove_discipline(self):
        if not self.confirm_discard_question():
            return
        name = self.current_discipline
        if not name:
            self.show_alert("Aviso", "Não há disciplina selecionada.", QMessageBox.Warning)
            return
        if not self.show_confirm("Remover disciplina", f"Remover '{name}' da lista? O arquivo será mantido no disco."):
            return
        other = next((item for item in self.config_data['disciplines'] if item != name), '')
        old_path = self.db_path
        candidate = storage_config.copy_config(self.config_data)
        storage_config.remove_discipline(candidate, name)
        if other:
            self.current_discipline = other
            self.db_path = self.config_data['disciplines'][other]
            if not self.switch_database_connection(candidate=candidate):
                self.current_discipline, self.db_path = name, old_path
                self.refresh_disciplines_dropdown()
                return
        else:
            if not self.save_global_config(candidate):
                return
            if self.conn:
                self.conn.close()
                self.conn = None
            self.current_discipline, self.db_path = '', ''
            self.selected_ids.clear()
            self.exam_order.synchronize(self.selected_ids)
            self.lbl_selected_count.setText("0 questão(ões) selecionada(s) para a prova")
            self.btn_delete_selected_questions.setEnabled(False)
            self.btn_browse_selected_questions.setEnabled(False)
            self.reset_question_form()
            self.reload_all_trees()
            while self.scroll_layout.count():
                widget = self.scroll_layout.takeAt(0).widget()
                if widget:
                    dispose_question_card(widget)
            self.search_view.apply(SearchFilters())
            self.lbl_result_range.setText("Nenhuma questão encontrada (0 questões)")
            self.lbl_page_count.setText("Página 0 de 0")
            self.btn_previous_page.setEnabled(False)
            self.btn_next_page.setEnabled(False)
            self.page_selector.setEnabled(False)
            self.setWindowTitle(APP_NAME)
        self.refresh_disciplines_dropdown()
        self.txt_db_path.setText(self.db_path)

    def action_backup_database(self):
        if not self.conn:
            self.show_alert("Aviso", "Abra um banco antes de fazer o backup.", QMessageBox.Warning)
            return
        stem = os.path.splitext(os.path.basename(self.db_path))[0]
        suggested = f"{stem}_backup_{datetime.now():%Y-%m-%d_%H%M}.db"
        destination, _ = QFileDialog.getSaveFileName(self, "Salvar backup", suggested, "SQLite Database (*.db)")
        if not destination:
            return
        try:
            storage_backup.manual(self.conn, destination)
        except FileExistsError:
            self.show_alert("Aviso", "Já existe um arquivo nesse local. Escolha outro nome para o backup.", QMessageBox.Warning)
            return
        except Exception as e:
            self.show_alert("Erro", f"Não foi possível criar o backup: {e}", QMessageBox.Critical)
            return
        self.show_alert("Backup concluído", f"Backup salvo em:\n{destination}", QMessageBox.Information)

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()
        if self.is_dark_mode:
            self.btn_toggle_theme.setText("Alternar para Modo Claro")
        else:
            self.btn_toggle_theme.setText("Alternar para Modo Escuro")

    # --- HIERARCHICAL TREE ENGINE ---
    def build_subject_tree(self, tree_widget):
        tree_widget.clear()
        if not self.conn: return
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, nome, parent_id FROM assuntos")
            all_rows = cursor.fetchall()
            roots = [r for r in all_rows if r[2] is None]
            children = [c for c in all_rows if c[2] is not None]
            
            def add_nodes(parent_item, parent_id):
                for child in [c for c in children if c[2] == parent_id]:
                    node = QTreeWidgetItem(parent_item)
                    node.setText(0, child[1])
                    node.setData(0, Qt.UserRole, child[0])
                    node.setCheckState(0, Qt.Unchecked)
                    add_nodes(node, child[0])

            for root in roots:
                node = QTreeWidgetItem(tree_widget)
                node.setText(0, root[1])
                node.setData(0, Qt.UserRole, root[0])
                node.setCheckState(0, Qt.Unchecked)
                add_nodes(node, root[0])
            tree_widget.resizeColumnToContents(0)
        except Exception as e:
            self.show_alert("Erro", f"Não foi possível carregar as categorias: {e}", QMessageBox.Warning)

    def configure_subject_tree_overflow(self, tree_widget):
        tree_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        tree_widget.setTextElideMode(Qt.ElideNone)
        tree_widget.header().setStretchLastSection(False)
        tree_widget.header().setSectionResizeMode(0, QHeaderView.Interactive)
        tree_widget.itemExpanded.connect(
            lambda _item, tree=tree_widget: QTimer.singleShot(
                0, lambda: tree.resizeColumnToContents(0)
            )
        )

    def reload_all_trees(self):
        self.build_subject_tree(self.tree_register_subjects)
        self.build_search_subjects_tree(self.tree_search_subjects)

    def filter_tree_by_text(self, text, tree_widget):
        search_token = text.lower().strip()
        def traverse_and_filter(item):
            item_match = search_token in item.text(0).lower()
            child_match = False
            for i in range(item.childCount()):
                if traverse_and_filter(item.child(i)):
                    child_match = True
            should_show = item_match or child_match
            item.setHidden(not should_show)
            if child_match and search_token:
                item.setExpanded(True)
            return should_show

        for i in range(tree_widget.topLevelItemCount()):
            traverse_and_filter(tree_widget.topLevelItem(i))

    def delete_selected_subject(self, tree_widget):
        selected_items = tree_widget.selectedItems()
        if not selected_items:
            self.show_alert("Aviso", "Por favor, selecione uma categoria clicando em seu texto antes de deletar.", QMessageBox.Warning)
            return
        target_item = selected_items[0]
        subject_name = target_item.text(0)
        subject_id = target_item.data(0, Qt.UserRole)
        
        if not subject_id:
            self.show_alert("Aviso", "Não é possível deletar a linha de agrupamento global.", QMessageBox.Warning)
            return

        confirm = self.show_confirm("Confirmar Exclusão", f"Tem certeza que deseja deletar a categoria '{subject_name}' e todas as suas subcategorias do banco?")
        if confirm:
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT id, nome, parent_id FROM assuntos")
                rows = cursor.fetchall()
                descendants = {subject_id}
                while True:
                    new_descendants = {
                        row_id for row_id, _, parent_id in rows
                        if parent_id in descendants and row_id not in descendants
                    }
                    if not new_descendants:
                        break
                    descendants.update(new_descendants)
                names_to_remove = {name for row_id, name, _ in rows if row_id in descendants}
                cursor.execute("SELECT id, assunto FROM questoes")
                for question_id, subject_string in cursor.fetchall():
                    names = [name.strip() for name in (subject_string or "").split(";")]
                    remaining = [name for name in names if name not in names_to_remove]
                    if remaining != names:
                        cursor.execute("UPDATE questoes SET assunto = ? WHERE id = ?", (";".join(remaining), question_id))
                cursor.execute("DELETE FROM assuntos WHERE id = ?", (subject_id,))
                self.conn.commit()
                self.show_alert("Sucesso", f"Categoria '{subject_name}' deletada!", QMessageBox.Information)
                self.reload_all_trees()
                self.load_questions(selected_only=self.search_view.selected_only)
            except Exception as e:
                self.conn.rollback()
                self.show_alert("Erro", f"Falha ao deletar:\n{str(e)}", QMessageBox.Critical)

    def open_add_subject_dialog(self):
        dlg = AddSubjectDialog(self, self.conn)
        dlg.setStyleSheet(self.styleSheet())
        if dlg.exec() == QDialog.Accepted:
            self.reload_all_trees()

    # --- TAB 1: REGISTER QUESTION WITH WYSIWYG ---
    def setup_tab_register(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(20)

        left_col = QVBoxLayout()
        left_col.setSpacing(9 if IS_WINDOWS else 12)

        def add_form_header(target_layout, text):
            header = QLabel(text)
            header.setObjectName("FilterHeaderLabel")
            header.setAlignment(Qt.AlignCenter)
            target_layout.addWidget(header)
            return header

        def add_form_divider(target_layout):
            divider = QFrame()
            divider.setObjectName("FilterSectionDivider")
            target_layout.addWidget(divider)
            return divider

        self.lbl_register_title = QLabel("Cadastrar Nova Questão")
        self.lbl_register_title.setObjectName("HeaderLabel")
        left_col.addWidget(self.lbl_register_title)
        self.btn_cancel_edit = QPushButton("Cancelar edição")
        self.btn_cancel_edit.clicked.connect(self.cancel_question_edit)
        self.btn_cancel_edit.hide()
        left_col.addWidget(self.btn_cancel_edit)
        add_form_header(left_col, "Classificação da Questão")

        row1 = QHBoxLayout()
        self.cb_type = InterfaceComboBox()
        configure_combo_popup(self.cb_type)
        self.cb_type.setItemDelegate(QStyledItemDelegate())
        self.cb_type.addItems(["Múltipla Escolha", "Dissertativa"])
        self.cb_type.currentTextChanged.connect(self.toggle_question_type)

        row1.addWidget(QLabel("Tipo:"))
        row1.addWidget(self.cb_type)
        row1.addWidget(QLabel("Dificuldade:"))
        self.diff_group = QButtonGroup(self)
        self.diff_radios = {}
        for index, label in enumerate(("Fácil", "Médio", "Difícil")):
            radio = QRadioButton(label)
            self.diff_group.addButton(radio, index)
            self.diff_radios[label] = radio
            row1.addWidget(radio)
        self.diff_radios["Médio"].setChecked(True)
        left_col.addLayout(row1)
        self.chk_keep_alternative_order = QCheckBox("Manter a ordem das alternativas")
        self.chk_keep_alternative_order.setToolTip("Não embaralhar as alternativas desta questão ao gerar versões.")
        left_col.addWidget(self.chk_keep_alternative_order)

        left_col.addWidget(QLabel("Segmento:"))
        segment_layout = QHBoxLayout()
        self.segment_group = QButtonGroup(self)
        self.segment_radios = {}
        for index, label in enumerate(("Ensino Fundamental", "Ensino Médio")):
            radio = QRadioButton(label)
            self.segment_group.addButton(radio, index)
            self.segment_radios[label] = radio
            segment_layout.addWidget(radio)
        segment_layout.addStretch()
        left_col.addLayout(segment_layout)
        self.segment_radios["Ensino Médio"].setChecked(True)
        self.segment_group.buttonToggled.connect(self.on_segment_changed)

        left_col.addWidget(QLabel("Ano / Série:"))
        self.year_options_layout = QHBoxLayout()
        self.year_group = QButtonGroup(self)
        self.year_group.setExclusive(False)
        self.year_checkboxes = {}
        left_col.addLayout(self.year_options_layout)
        self.populate_year_options("Ensino Médio")
        for checkbox in self.year_checkboxes.values():
            checkbox.setChecked(True)

        source_row = QHBoxLayout()
        source_column = QVBoxLayout()
        self.txt_question_source = QLineEdit()
        self.txt_question_source.setPlaceholderText("Ex.: ENEM, FUVEST, livro…")
        source_label = QLabel("Fonte da Questão (opcional):")
        source_label.setBuddy(self.txt_question_source)
        source_column.addWidget(source_label)
        source_column.addWidget(self.txt_question_source)
        source_row.addLayout(source_column, stretch=1)

        source_year_column = QVBoxLayout()
        self.txt_source_year = QLineEdit()
        self.txt_source_year.setPlaceholderText("Ex.: 2024")
        self.txt_source_year.setMaximumWidth(140)
        source_year_label = QLabel("Ano (opcional):")
        source_year_label.setBuddy(self.txt_source_year)
        source_year_column.addWidget(source_year_label)
        source_year_column.addWidget(self.txt_source_year)
        source_row.addLayout(source_year_column)
        left_col.addLayout(source_row)

        add_form_divider(left_col)
        add_form_header(left_col, "Enunciado da Questão")

        self.prompt_editor_panel = QFrame()
        self.prompt_editor_panel.setObjectName("RichTextEditorPanel")
        prompt_panel_layout = QVBoxLayout(self.prompt_editor_panel)
        prompt_panel_layout.setContentsMargins(0, 0, 0, 0)
        prompt_panel_layout.setSpacing(0)

        # Unified rich-text toolbar
        self.format_toolbar = QFrame()
        self.format_toolbar.setObjectName("FormattingToolbar")
        toolbar_layout = QHBoxLayout(self.format_toolbar)
        toolbar_layout.setContentsMargins(6, 3 if IS_WINDOWS else 4, 6, 3 if IS_WINDOWS else 4)
        toolbar_layout.setSpacing(3)

        self.btn_bold = QToolButton()
        self.btn_bold.setText("B")
        self.btn_bold.setFont(QFont("Arial", 12, QFont.Bold))
        self.btn_bold.setCheckable(True)
        self.btn_bold.setToolTip("Negrito")
        self.btn_bold.clicked.connect(self.set_text_bold)

        self.btn_italic = QToolButton()
        self.btn_italic.setText("I")
        self.btn_italic.setFont(QFont("Arial", 12, QFont.Medium, True))
        self.btn_italic.setCheckable(True)
        self.btn_italic.setToolTip("Itálico")
        self.btn_italic.clicked.connect(self.set_text_italic)

        self.btn_underline = QToolButton()
        self.btn_underline.setText("U")
        font_u = QFont("Arial", 12)
        font_u.setUnderline(True)
        self.btn_underline.setFont(font_u)
        self.btn_underline.setCheckable(True)
        self.btn_underline.setToolTip("Sublinhado")
        self.btn_underline.clicked.connect(self.set_text_underline)

        self.btn_superscript = QToolButton()
        self.btn_superscript.setText("x²")
        self.btn_superscript.setFont(QFont("Arial", 11))
        self.btn_superscript.setCheckable(True)
        self.btn_superscript.setToolTip("Sobrescrito")
        self.btn_superscript.clicked.connect(self.set_text_superscript)

        self.btn_subscript = QToolButton()
        self.btn_subscript.setText("x₂")
        self.btn_subscript.setFont(QFont("Arial", 11))
        self.btn_subscript.setCheckable(True)
        self.btn_subscript.setToolTip("Subscrito")
        self.btn_subscript.clicked.connect(self.set_text_subscript)

        self.btn_strikethrough = QToolButton()
        self.btn_strikethrough.setText("S̶")
        self.btn_strikethrough.setFont(QFont("Arial", 12))
        self.btn_strikethrough.setCheckable(True)
        self.btn_strikethrough.setToolTip("Tachado")
        self.btn_strikethrough.clicked.connect(self.set_text_strikethrough)

        format_buttons = (
            self.btn_bold, self.btn_italic, self.btn_underline,
            self.btn_superscript, self.btn_subscript, self.btn_strikethrough,
        )
        for button in format_buttons:
            button.setAutoRaise(True)
            toolbar_layout.addWidget(button)
        for button, name in zip(format_buttons, ("bold", "italic", "underline", "superscript", "subscript", "strike")):
            set_ui_icon(button, name)

        separator_one = QFrame()
        separator_one.setObjectName("ToolbarSeparator")
        separator_one.setFixedHeight(24)
        toolbar_layout.addWidget(separator_one)

        self.btn_add_equation = QToolButton()
        self.btn_add_equation.setObjectName("InsertToolButton")
        self.btn_add_equation.setText("∑")
        self.btn_add_equation.setToolTip("Inserir equação")
        self.btn_add_equation.setAccessibleName("Inserir equação")
        self.btn_add_equation.setAutoRaise(True)
        self.btn_add_equation.clicked.connect(self.insert_equation)

        self.btn_add_img = QToolButton()
        self.btn_add_img.setObjectName("InsertToolButton")
        self.btn_add_img.setText("▧")
        self.btn_add_img.setToolTip("Inserir imagem")
        self.btn_add_img.setAccessibleName("Inserir imagem")
        self.btn_add_img.setAutoRaise(True)
        self.btn_add_img.clicked.connect(self.insert_image_to_prompt)
        set_ui_icon(self.btn_add_equation, "equation")
        set_ui_icon(self.btn_add_img, "image")

        toolbar_layout.addWidget(self.btn_add_equation)
        toolbar_layout.addWidget(self.btn_add_img)
        prompt_panel_layout.addWidget(self.format_toolbar)

        self.txt_prompt = ClipboardRichTextEdit(initial_height=170, minimum_height=170)
        self.txt_prompt.setPlaceholderText("Digite ou cole o enunciado. Imagens, formatação e fórmulas são aceitas.")
        self.txt_prompt.cursorPositionChanged.connect(self.update_toolbar_states)
        prompt_panel_layout.addWidget(self.txt_prompt)
        left_col.addWidget(self.prompt_editor_panel)

        self.alts_divider = add_form_divider(left_col)
        self.alts_header = add_form_header(left_col, "Alternativas")

        self.alts_container = QFrame()
        self.alts_container.setObjectName("AltsContainer")
        alts_layout = QVBoxLayout(self.alts_container)
        alt_margin = 12 if IS_WINDOWS else 15
        alts_layout.setContentsMargins(alt_margin, alt_margin, alt_margin, alt_margin)
        alts_layout.setSpacing(10)
        
        self.alt_inputs = {}
        self.alt_radios = QButtonGroup(self)
        self.alt_radios.setExclusive(True)

        for letter in ['A', 'B', 'C', 'D', 'E']:
            row = QHBoxLayout()
            lbl = QLabel(f"{letter})")
            txt = ClipboardRichTextEdit(initial_height=54, minimum_height=54)
            txt.setPlaceholderText(f"Alternativa {letter} (cole texto ou imagem)...")
            txt.setAcceptRichText(True)
            chk = QCheckBox("Correta")
            
            row.addWidget(lbl, alignment=Qt.AlignTop)
            row.addWidget(txt, stretch=1)
            row.addWidget(chk)
            alts_layout.addLayout(row)
            
            self.alt_inputs[letter] = txt
            self.alt_radios.addButton(chk, ord(letter))

        left_col.addWidget(self.alts_container)

        self.essay_container = QWidget()
        essay_layout = QVBoxLayout(self.essay_container)
        essay_layout.setContentsMargins(0, 0, 0, 0)
        add_form_header(essay_layout, "Gabarito / Resolução Esperada")
        self.txt_essay_answer = ClipboardRichTextEdit(initial_height=130, minimum_height=130)
        essay_layout.addWidget(self.txt_essay_answer)
        left_col.addWidget(self.essay_container)
        self.essay_container.setVisible(False)

        btn_save = QPushButton("Salvar Questão")
        btn_save.setObjectName("PrimaryButton")
        btn_save.clicked.connect(self.save_question)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        left_col.addLayout(btn_layout)

        right_col = QVBoxLayout()
        right_col.setSpacing(10)
        add_form_header(right_col, "Categorias / Assuntos Vinculados")
        
        self.txt_filter_reg_subjects = QLineEdit()
        self.txt_filter_reg_subjects.setPlaceholderText("Buscar categoria..." if IS_WINDOWS else "🔎 Buscar categoria...")
        if IS_WINDOWS:
            self.txt_filter_reg_subjects.addAction(ui_icon("search"), QLineEdit.LeadingPosition)
        self.txt_filter_reg_subjects.textChanged.connect(
            lambda t: self.filter_tree_by_text(t, self.tree_register_subjects)
        )
        right_col.addWidget(self.txt_filter_reg_subjects)
        
        self.tree_register_subjects = QTreeWidget()
        self.tree_register_subjects.setHeaderHidden(True)
        self.configure_subject_tree_overflow(self.tree_register_subjects)
        right_col.addWidget(self.tree_register_subjects)
        
        actions_sub_layout = QHBoxLayout()
        btn_new_subject = QPushButton("Adicionar" if IS_WINDOWS else "＋ Adicionar")
        btn_new_subject.setObjectName("PrimaryButton")
        set_ui_icon(btn_new_subject, "add")
        btn_new_subject.clicked.connect(self.open_add_subject_dialog)
        
        btn_del_subject = QPushButton("Deletar Categoria" if IS_WINDOWS else "🗑 Deletar Categoria")
        btn_del_subject.setObjectName("DangerButton")
        set_ui_icon(btn_del_subject, "trash")
        btn_del_subject.clicked.connect(lambda: self.delete_selected_subject(self.tree_register_subjects))
        
        actions_sub_layout.addWidget(btn_new_subject)
        actions_sub_layout.addWidget(btn_del_subject)
        right_col.addLayout(actions_sub_layout)

        left_content = QWidget()
        left_content.setObjectName("RegisterScrollContent")
        left_content.setLayout(left_col)
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QFrame.NoFrame)
        left_scroll.setWidget(left_content)
        layout.addWidget(left_scroll, stretch=2)
        layout.addLayout(right_col, stretch=1)
        self.tabs.addTab(tab, "Cadastrar Questão")

    # --- TEXT FORMATTING LOGIC ---
    def eventFilter(self, watched, event):
        if event.type() == QEvent.FocusIn and watched in (self.txt_prompt, *self.alt_inputs.values(), self.txt_essay_answer):
            self._active_editor = watched
            self.update_toolbar_states()
        return super().eventFilter(watched, event)

    def set_text_bold(self):
        cursor = self._active_editor.textCursor()
        fmt = cursor.charFormat()
        fmt.setFontWeight(QFont.Bold if self.btn_bold.isChecked() else QFont.Normal)
        cursor.mergeCharFormat(fmt)
        self._active_editor.mergeCurrentCharFormat(fmt)

    def set_text_italic(self):
        cursor = self._active_editor.textCursor()
        fmt = cursor.charFormat()
        fmt.setFontItalic(self.btn_italic.isChecked())
        cursor.mergeCharFormat(fmt)
        self._active_editor.mergeCurrentCharFormat(fmt)

    def set_text_underline(self):
        cursor = self._active_editor.textCursor()
        fmt = cursor.charFormat()
        fmt.setFontUnderline(self.btn_underline.isChecked())
        cursor.mergeCharFormat(fmt)
        self._active_editor.mergeCurrentCharFormat(fmt)

    def set_text_superscript(self):
        cursor = self._active_editor.textCursor()
        fmt = cursor.charFormat()
        if self.btn_superscript.isChecked():
            self.btn_subscript.setChecked(False)
            fmt.setVerticalAlignment(QTextCharFormat.AlignSuperScript)
        else:
            fmt.setVerticalAlignment(QTextCharFormat.AlignNormal)
        cursor.mergeCharFormat(fmt)
        self._active_editor.mergeCurrentCharFormat(fmt)

    def set_text_subscript(self):
        cursor = self._active_editor.textCursor()
        fmt = cursor.charFormat()
        if self.btn_subscript.isChecked():
            self.btn_superscript.setChecked(False)
            fmt.setVerticalAlignment(QTextCharFormat.AlignSubScript)
        else:
            fmt.setVerticalAlignment(QTextCharFormat.AlignNormal)
        cursor.mergeCharFormat(fmt)
        self._active_editor.mergeCurrentCharFormat(fmt)

    def set_text_strikethrough(self):
        cursor = self._active_editor.textCursor()
        fmt = cursor.charFormat()
        fmt.setFontStrikeOut(self.btn_strikethrough.isChecked())
        cursor.mergeCharFormat(fmt)
        self._active_editor.mergeCurrentCharFormat(fmt)

    def update_toolbar_states(self):
        cursor = self._active_editor.textCursor()
        fmt = cursor.charFormat()
        self.btn_bold.setChecked(fmt.fontWeight() == QFont.Bold)
        self.btn_italic.setChecked(fmt.fontItalic())
        self.btn_underline.setChecked(fmt.fontUnderline())
        self.btn_strikethrough.setChecked(fmt.fontStrikeOut())
        self.btn_superscript.setChecked(fmt.verticalAlignment() == QTextCharFormat.AlignSuperScript)
        self.btn_subscript.setChecked(fmt.verticalAlignment() == QTextCharFormat.AlignSubScript)

    def insert_equation(self):
        dlg = InsertEquationDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return
        expression = dlg.get_equation_text()
        if not expression:
            return
        html_equation = self.format_equation_html(expression, dlg.get_equation_type())
        cursor = self._active_editor.textCursor()
        cursor.insertHtml(html_equation)

    def format_equation_html(self, text, equation_type="Matemática"):
        return format_equation_html(text, equation_type)

    def insert_image_to_prompt(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Imagem", "", "Imagens (*.png *.jpg *.jpeg *.bmp)"
        )
        if not file_path: return

        image = QImage(file_path)
        if image.isNull():
            self.show_alert("Erro", "Falha ao carregar arquivo de imagem válido.", QMessageBox.Warning)
            return

        if image.width() > 500:
            image = image.scaledToWidth(500, Qt.SmoothTransformation)

        ba = QByteArray()
        buffer = QBuffer(ba)
        buffer.open(QIODevice.WriteOnly)
        image.save(buffer, "PNG")
        base64_data = ba.toBase64().data().decode("utf-8")
        src_url = f"data:image/png;base64,{base64_data}"

        cursor = self.txt_prompt.textCursor()
        image_format = QTextImageFormat()
        image_format.setName(src_url)
        image_format.setWidth(image.width())
        image_format.setHeight(image.height())
        cursor.insertImage(image_format)

    def get_checked_subjects(self, tree_widget):
        checked_names = []
        def traverse(item):
            if item.checkState(0) == Qt.Checked and item.text(0) != "Todas as Categorias":
                checked_names.append(item.text(0))
            for i in range(item.childCount()):
                traverse(item.child(i))
        for i in range(tree_widget.topLevelItemCount()):
            traverse(tree_widget.topLevelItem(i))
        return checked_names

    def toggle_question_type(self, q_type):
        if hasattr(self, 'chk_keep_alternative_order'):
            self.chk_keep_alternative_order.setEnabled(q_type == "Múltipla Escolha")
        if q_type == "Múltipla Escolha":
            self.alts_divider.setVisible(True)
            self.alts_header.setVisible(True)
            self.alts_container.setVisible(True)
            self.essay_container.setVisible(False)
        else:
            self.alts_divider.setVisible(False)
            self.alts_header.setVisible(False)
            self.alts_container.setVisible(False)
            self.essay_container.setVisible(True)

    def populate_year_options(self, segment):
        while self.year_options_layout.count():
            item = self.year_options_layout.takeAt(0)
            widget = item.widget()
            if widget:
                self.year_group.removeButton(widget)
                widget.hide()
                widget.deleteLater()
        self.year_checkboxes.clear()

        if segment == "Ensino Fundamental":
            labels = ("6º Ano", "7º Ano", "8º Ano", "9º Ano")
        else:
            labels = ("1ª Série", "2ª Série", "3ª Série")

        for index, label in enumerate(labels):
            checkbox = QCheckBox(label)
            checkbox.setStyle(self._selection_style)
            self.year_group.addButton(checkbox, index)
            self.year_checkboxes[label] = checkbox
            self.year_options_layout.addWidget(checkbox)
        self.year_options_layout.addStretch()

    def on_segment_changed(self, button, checked):
        if checked:
            self.populate_year_options(button.text())

    @staticmethod
    def checked_radio_text(group):
        button = group.checkedButton()
        return button.text() if button else ""

    @staticmethod
    def parse_question_year_values(year_value, segment=""):
        return parse_question_year_values(year_value, segment)

    @staticmethod
    def format_question_year_info(year_value, segment):
        return format_question_year_info(year_value, segment)

    def setup_checkbox_filter(self, group, all_label):
        group.setExclusive(False)
        all_checkbox = next(button for button in group.buttons() if button.text() == all_label)
        for checkbox in group.buttons():
            checkbox.toggled.connect(
                lambda checked, current=checkbox: self.on_filter_checkbox_toggled(
                    group, all_checkbox, current, checked
                )
            )

    @staticmethod
    def on_filter_checkbox_toggled(group, all_checkbox, current, checked):
        if not checked:
            return
        if current is all_checkbox:
            for checkbox in group.buttons():
                if checkbox is not all_checkbox:
                    checkbox.setChecked(False)
        else:
            all_checkbox.setChecked(False)

    @staticmethod
    def checked_filter_values(group, all_label):
        return [
            checkbox.text() for checkbox in group.buttons()
            if checkbox.isChecked() and checkbox.text() != all_label
        ]

    def question_draft_from_form(self):
        def content(editor):
            return RichContent(editor.toHtml(), bool(editor.toPlainText().strip()))
        checked = self.alt_radios.checkedButton()
        return QuestionDraft(
            categories=tuple(self.get_checked_subjects(self.tree_register_subjects)),
            difficulty=self.checked_radio_text(self.diff_group), kind=self.cb_type.currentText(),
            statement=content(self.txt_prompt),
            years=tuple(label for label, checkbox in self.year_checkboxes.items() if checkbox.isChecked()),
            segment=self.checked_radio_text(self.segment_group),
            alternatives=tuple(content(self.alt_inputs[letter]) for letter in 'ABCDE'),
            answer=chr(self.alt_radios.id(checked)) if checked else '',
            essay_answer=content(self.txt_essay_answer),
            source=self.txt_question_source.text(), source_year=self.txt_source_year.text(),
            keep_alternative_order=self.chk_keep_alternative_order.isChecked(),
        )

    def save_question(self):
        if not self.conn:
            self.show_alert("Erro", "O banco de dados não está conectado.", QMessageBox.Critical)
            return
        draft = self.question_draft_from_form()
        try:
            validate_question(draft)
        except QuestionValidationError as error:
            messages = {
                'categories': "Selecione ao menos uma categoria na árvore lateral.",
                'years': "Selecione o segmento e ao menos um ano/série.",
                'statement': "O campo 'Enunciado' não pode estar vazio.",
                'answer': "Selecione uma alternativa como Correta.",
                'alternatives': "Preencha todas as alternativas.",
                'alternative': f"A alternativa {error.letter} está vazia.",
            }
            self.show_alert("Aviso", messages[error.code], QMessageBox.Warning)
            return
        try:
            session = self.question_session
            unchanged = session.unchanged_values(draft) if session else None
            if session:
                draft = session.prepare(draft)
            if session and session.mode == 'edit':
                update_question(self.conn, session.question_id, draft, unchanged)
            else:
                insert_question(self.conn, draft, unchanged)
            self.show_alert("Sucesso", "Questão salva com sucesso!", QMessageBox.Information)
            self.question_session = None
            self.lbl_register_title.setText("Cadastrar Nova Questão")
            self.btn_cancel_edit.hide()
            self.clear_register_form()
            self.load_questions(selected_only=self.search_view.selected_only)
        except Exception as e:
            self.show_alert("Erro", f"Falha ao salvar no banco:\n{str(e)}", QMessageBox.Critical)

    def reset_question_form(self):
        self.question_session = None
        self.lbl_register_title.setText("Cadastrar Nova Questão")
        self.btn_cancel_edit.hide()
        self.clear_register_form()

    def confirm_discard_question(self):
        current = self.question_draft_from_form()
        session = self.question_session
        dirty = session.is_dirty(current) if session else current != self.form_snapshot
        return not dirty or self.show_confirm("Descartar alterações", "Há alterações não salvas na questão. Deseja descartá-las?")

    def closeEvent(self, event):
        if not self.confirm_discard_question():
            event.ignore()
            return
        super().closeEvent(event)

    def cancel_question_edit(self):
        if not self.confirm_discard_question():
            return
        self.question_session = None
        self.lbl_register_title.setText("Cadastrar Nova Questão")
        self.btn_cancel_edit.hide()
        self.clear_register_form()

    def open_question_for_edit(self, question_id, duplicate=False):
        if not self.conn or not self.confirm_discard_question():
            return
        try:
            row = get_question(self.conn, question_id)
            if row is None:
                self.show_alert("Aviso", "A questão não foi encontrada.", QMessageBox.Warning)
                return
            self.clear_register_form()
            self.cb_type.setCurrentText(row['tipo'] or '')
            if row['dificuldade'] in self.diff_radios:
                self.diff_radios[row['dificuldade']].setChecked(True)
            segment, years = stored_school_years(row['ano_sugerido'], row['segmento'])
            if segment in self.segment_radios:
                self.segment_radios[segment].setChecked(True)
            for label, checkbox in self.year_checkboxes.items():
                checkbox.setChecked(label in years)
            self.txt_question_source.setText(row['fonte_questao'] or '')
            self.txt_source_year.setText(row['ano_origem'] or '')
            self.chk_keep_alternative_order.setChecked(bool(row['keep_alternative_order']))
            self.txt_prompt.setHtml(row['enunciado'] or '')
            for letter, editor in self.alt_inputs.items():
                editor.setHtml(row[f'alternativa_{letter.lower()}'] or '')
            if row['tipo'] == 'Múltipla Escolha':
                button = self.alt_radios.button(ord((row['gabarito'] or ' ').strip().upper()[:1] or ' '))
                if button:
                    button.setChecked(True)
                self.txt_essay_answer.clear()
            else:
                self.txt_essay_answer.setHtml(row['gabarito'] or '')
            items = []
            def visit(item):
                items.append(item)
                for index in range(item.childCount()):
                    visit(item.child(index))
            for index in range(self.tree_register_subjects.topLevelItemCount()):
                visit(self.tree_register_subjects.topLevelItem(index))
            present, missing = split_available_categories(row['assunto'], (item.text(0) for item in items))
            for item in items:
                item.setCheckState(0, Qt.Checked if item.text(0) in present else Qt.Unchecked)
            initial = self.question_draft_from_form()
            original = replace(initial,
                statement=RichContent(row['enunciado'] or '', initial.statement.has_text),
                alternatives=tuple(RichContent(row[f'alternativa_{letter.lower()}'] or '', original.has_text)
                                   for letter, original in zip('ABCDE', initial.alternatives)),
                essay_answer=RichContent((row['gabarito'] or '') if row['tipo'] != 'Múltipla Escolha' else '',
                                         initial.essay_answer.has_text))
            self.question_session = QuestionSession('duplicate' if duplicate else 'edit', question_id, initial, original, row, missing)
            self.lbl_register_title.setText("Duplicar Questão" if duplicate else f"Editando questão {question_id}")
            self.btn_cancel_edit.setVisible(True)
            self.tabs.setCurrentIndex(0)
            if missing:
                self.show_alert("Categorias não encontradas", "Categorias não encontradas: " + ', '.join(missing), QMessageBox.Warning)
        except Exception as e:
            self.show_alert("Erro", f"Não foi possível carregar a questão: {e}", QMessageBox.Critical)

    def clear_register_form(self):
        self.chk_keep_alternative_order.setChecked(False)
        self.txt_question_source.clear()
        self.txt_source_year.clear()
        self.txt_prompt.clear()
        self.txt_essay_answer.clear()
        for txt in self.alt_inputs.values():
            txt.clear()
        
        self.alt_radios.setExclusive(False)
        checked = self.alt_radios.checkedButton()
        if checked:
            checked.setChecked(False)
        self.alt_radios.setExclusive(True)
        
        def uncheck_all(item):
            item.setCheckState(0, Qt.Unchecked)
            for i in range(item.childCount()):
                uncheck_all(item.child(i))
        for i in range(self.tree_register_subjects.topLevelItemCount()):
            uncheck_all(self.tree_register_subjects.topLevelItem(i))
        self.form_snapshot = self.question_draft_from_form()

    # --- TAB 2: SEARCH & SELECT QUESTIONS ---
    def setup_tab_search(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(15)

        filter_panel = QVBoxLayout()
        filter_panel.setSpacing(10)

        def add_filter_header(text):
            header = QLabel(text)
            header.setObjectName("FilterHeaderLabel")
            header.setAlignment(Qt.AlignCenter)
            filter_panel.addWidget(header)
        
        add_filter_header("Filtrar por Categoria:")
        self.txt_filter_search_subjects = QLineEdit()
        self.txt_filter_search_subjects.setPlaceholderText("Buscar categoria..." if IS_WINDOWS else "🔎 Buscar categoria...")
        if IS_WINDOWS:
            self.txt_filter_search_subjects.addAction(ui_icon("search"), QLineEdit.LeadingPosition)
        self.txt_filter_search_subjects.textChanged.connect(
            lambda t: self.filter_tree_by_text(t, self.tree_search_subjects)
        )
        filter_panel.addWidget(self.txt_filter_search_subjects)
        
        self.tree_search_subjects = ResizableTreeWidget(initial_height=220, minimum_height=220)
        self.tree_search_subjects.setHeaderHidden(True)
        self.configure_subject_tree_overflow(self.tree_search_subjects)
        filter_panel.addWidget(self.tree_search_subjects)
        
        btn_del_search_tab = QPushButton("Deletar Categoria Selecionada" if IS_WINDOWS else "🗑 Deletar Categoria Selecionada")
        btn_del_search_tab.setObjectName("DangerButton")
        set_ui_icon(btn_del_search_tab, "trash")
        btn_del_search_tab.clicked.connect(lambda: self.delete_selected_subject(self.tree_search_subjects))
        filter_panel.addWidget(btn_del_search_tab)

        add_filter_header("Buscar no Enunciado (Texto):")
        self.txt_search_question_text = QLineEdit()
        self.txt_search_question_text.setPlaceholderText("Ex: revolução, equação...")
        filter_panel.addWidget(self.txt_search_question_text)

        add_filter_header("Fonte da Questão:")
        self.txt_search_question_source = QLineEdit()
        self.txt_search_question_source.setPlaceholderText("Ex.: ENEM (parte do nome)")
        self.txt_search_question_source.setToolTip("Deixe vazio para buscar em todas as fontes.")
        self.txt_search_question_source.returnPressed.connect(self.show_filtered_questions)
        filter_panel.addWidget(self.txt_search_question_source)

        add_filter_header("Ano da Fonte:")
        source_year_row = QHBoxLayout()
        self.txt_search_source_year_from = QLineEdit()
        self.txt_search_source_year_to = QLineEdit()
        for label_text, field in (("Desde", self.txt_search_source_year_from),
                                  ("até", self.txt_search_source_year_to)):
            label = QLabel(label_text)
            label.setBuddy(field)
            field.setAccessibleName(f"Ano da fonte {label_text}")
            field.setPlaceholderText("Ex.: 2022")
            field.setToolTip("Ano da fonte; deixe vazio para não limitar este lado do intervalo.")
            field.returnPressed.connect(self.show_filtered_questions)
            source_year_row.addWidget(label)
            source_year_row.addWidget(field)
        filter_panel.addLayout(source_year_row)

        add_filter_header("Dificuldade:")
        self.search_diff_group = QButtonGroup(self)
        diff_grid = QGridLayout()
        self.search_diff_checkboxes = {}
        for index, label in enumerate(("Todas as Dificuldades", "Fácil", "Médio", "Difícil")):
            checkbox = QCheckBox(label)
            self.search_diff_group.addButton(checkbox, index)
            self.search_diff_checkboxes[label] = checkbox
            diff_grid.addWidget(checkbox, index // 2, index % 2)
        self.search_diff_checkboxes["Todas as Dificuldades"].setChecked(True)
        self.setup_checkbox_filter(self.search_diff_group, "Todas as Dificuldades")
        filter_panel.addLayout(diff_grid)
        difficulty_divider = QFrame()
        difficulty_divider.setObjectName("FilterSectionDivider")
        difficulty_divider.setFixedHeight(3)
        filter_panel.addWidget(difficulty_divider)

        add_filter_header("Ano / Série Escolar:")
        self.search_year_group = QButtonGroup(self)
        year_filter_layout = QVBoxLayout()
        self.search_year_checkboxes = {}
        all_years = QCheckBox("Todos os Anos")
        self.search_year_group.addButton(all_years, 0)
        self.search_year_checkboxes["Todos os Anos"] = all_years
        year_filter_layout.addWidget(all_years)

        fundamental_label = QLabel("Ensino Fundamental")
        fundamental_label.setObjectName("YearSegmentLabel")
        year_filter_layout.addWidget(fundamental_label)
        fundamental_grid = QGridLayout()
        for index, label in enumerate(("6º Ano", "7º Ano", "8º Ano", "9º Ano")):
            checkbox = QCheckBox(label)
            self.search_year_group.addButton(checkbox, index + 1)
            self.search_year_checkboxes[label] = checkbox
            fundamental_grid.addWidget(checkbox, index // 2, index % 2)
        year_filter_layout.addLayout(fundamental_grid)

        divider = QFrame()
        divider.setObjectName("YearSegmentDivider")
        divider.setFixedHeight(1)
        year_filter_layout.addWidget(divider)

        high_school_label = QLabel("Ensino Médio")
        high_school_label.setObjectName("YearSegmentLabel")
        year_filter_layout.addWidget(high_school_label)
        high_school_grid = QGridLayout()
        for index, label in enumerate(("1ª Série", "2ª Série", "3ª Série")):
            checkbox = QCheckBox(label)
            self.search_year_group.addButton(checkbox, index + 5)
            self.search_year_checkboxes[label] = checkbox
            high_school_grid.addWidget(checkbox, index, 0)
        year_filter_layout.addLayout(high_school_grid)

        all_years.setChecked(True)
        self.setup_checkbox_filter(self.search_year_group, "Todos os Anos")
        filter_panel.addLayout(year_filter_layout)
        year_type_divider = QFrame()
        year_type_divider.setObjectName("FilterSectionDivider")
        year_type_divider.setFixedHeight(3)
        filter_panel.addWidget(year_type_divider)
        
        add_filter_header("Tipo:")
        self.search_type_group = QButtonGroup(self)
        type_grid = QGridLayout()
        self.search_type_checkboxes = {}
        for index, label in enumerate(("Todos os Tipos", "Múltipla Escolha", "Dissertativa")):
            checkbox = QCheckBox(label)
            self.search_type_group.addButton(checkbox, index)
            self.search_type_checkboxes[label] = checkbox
            type_grid.addWidget(checkbox, index // 2, index % 2)
        self.search_type_checkboxes["Todos os Tipos"].setChecked(True)
        self.setup_checkbox_filter(self.search_type_group, "Todos os Tipos")
        filter_panel.addLayout(type_grid)
        
        btn_filter = QPushButton("Filtrar Questões")
        btn_filter.setObjectName("PrimaryButton")
        btn_filter.clicked.connect(self.show_filtered_questions)
        filter_panel.addWidget(btn_filter)

        results_panel = QVBoxLayout()
        results_header = QHBoxLayout()
        self.lbl_selected_count = QLabel("0 questão(ões) selecionada(s) para a prova")
        self.lbl_selected_count.setObjectName("HeaderLabel")
        results_header.addWidget(self.lbl_selected_count, stretch=1)
        self.btn_browse_selected_questions = QPushButton("Navegar pelas questões selecionadas")
        self.btn_browse_selected_questions.setObjectName("BrowseSelectedButton")
        self.btn_browse_selected_questions.setCheckable(True)
        self.btn_browse_selected_questions.setEnabled(False)
        self.btn_browse_selected_questions.toggled.connect(self.toggle_selected_question_view)
        results_header.addWidget(self.btn_browse_selected_questions)
        results_panel.addLayout(results_header)
        self.btn_delete_selected_questions = QPushButton("Excluir questões selecionadas")
        self.btn_delete_selected_questions.setObjectName("DangerButton")
        self.btn_delete_selected_questions.setEnabled(False)
        self.btn_delete_selected_questions.clicked.connect(self.delete_selected_questions)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("QuestionResultsContent")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll_layout.setSpacing(10)
        self.scroll_layout.setContentsMargins(5, 5, 5, 5)
        self.scroll_area.setWidget(self.scroll_content)
        results_panel.addWidget(self.scroll_area, stretch=1)
        pager = QHBoxLayout()
        self.lbl_result_range = QLabel("Nenhuma questão encontrada")
        pager.addWidget(self.lbl_result_range, stretch=1)
        self.btn_previous_page = QPushButton("Anterior")
        self.btn_previous_page.clicked.connect(lambda: self.move_search_page(self.search_view.page - 1))
        pager.addWidget(self.btn_previous_page)
        self.page_selector = QSpinBox()
        self.page_selector.setMinimum(1)
        self.page_selector.valueChanged.connect(self.move_search_page)
        pager.addWidget(self.page_selector)
        self.lbl_page_count = QLabel("Página 0 de 0")
        pager.addWidget(self.lbl_page_count)
        self.btn_next_page = QPushButton("Próxima")
        self.btn_next_page.clicked.connect(lambda: self.move_search_page(self.search_view.page + 1))
        pager.addWidget(self.btn_next_page)
        results_panel.addLayout(pager)
        delete_button_row = QHBoxLayout()
        delete_button_row.addStretch()
        delete_button_row.addWidget(self.btn_delete_selected_questions)
        results_panel.addLayout(delete_button_row)

        filter_content = QWidget()
        filter_content.setObjectName("SearchFilterContent")
        filter_content.setLayout(filter_panel)
        filter_scroll = QScrollArea()
        filter_scroll.setWidgetResizable(True)
        filter_scroll.setFrameShape(QFrame.NoFrame)
        filter_scroll.setWidget(filter_content)
        layout.addWidget(filter_scroll, stretch=1)
        layout.addLayout(results_panel, stretch=2)
        self.tabs.addTab(tab, "Buscar e Selecionar Questões")

    def build_search_subjects_tree(self, tree_widget):
        self.build_subject_tree(tree_widget)
        all_item = QTreeWidgetItem()
        all_item.setText(0, "Todas as Categorias")
        all_item.setCheckState(0, Qt.Checked)
        tree_widget.insertTopLevelItem(0, all_item)
        tree_widget.resizeColumnToContents(0)

    @staticmethod
    def html_fragment(value):
        return html_fragment(value)

    def move_search_page(self, page):
        previous = self.search_view.page
        self.search_view.page = page
        if not self.load_questions(selected_only=self.search_view.selected_only):
            self.search_view.page = previous
            self.page_selector.blockSignals(True)
            self.page_selector.setValue(max(1, previous))
            self.page_selector.blockSignals(False)
        else:
            self.scroll_area.verticalScrollBar().setValue(0)

    def load_questions(self, selected_only=False):
        cards = []
        try:
            bounds, results = page_questions(
                self.conn, self.search_view.applied, self.search_view.page,
                self.selected_ids if selected_only else None)

            for row in results:
                q_id, sub, dif, ano, segment, q_type, html_prompt = row[:7]
                alternatives = row[7:12]
                expected_answer = row[12]
                question_source, question_source_year = row[13:15]

                is_checked = q_id in self.selected_ids
                
                year_label = self.format_question_year_info(ano, segment)
                content_parts = [self.html_fragment(html_prompt)]
                if q_type == "Múltipla Escolha":
                    content_parts.append("<hr><p><b>Alternativas:</b></p>")
                    correct_letter = str(expected_answer or "").strip().upper()
                    option_rows = ['<table border="0" cellspacing="0" cellpadding="4">']
                    for letter, alternative in zip("ABCDE", alternatives):
                        alternative_html = self.html_fragment(alternative)
                        if letter == correct_letter:
                            option_rows.append(
                                f'<tr bgcolor="#DCFCE7"><td width="28" valign="top" bgcolor="#DCFCE7">'
                                f'<b style="color:#166534;">✓</b></td><td bgcolor="#DCFCE7" style="color:#166534;">'
                                f"<b>{letter})</b> {alternative_html}</td></tr>"
                            )
                        else:
                            option_rows.append(
                                f'<tr><td width="28" valign="top">&nbsp;</td><td>'
                                f"<b>{letter})</b> {alternative_html}</td></tr>"
                            )
                    option_rows.append("</table>")
                    content_parts.append("".join(option_rows))
                elif q_type == "Dissertativa":
                    content_parts.append("<hr><p><b>Gabarito Esperado:</b></p>")
                    if expected_answer and expected_answer.strip():
                        content_parts.append(self.html_fragment(expected_answer))
                    else:
                        content_parts.append("<p>Resposta esperada não registrada</p>")
                card_html = "<html><body>" + "".join(content_parts) + "</body></html>"
                card = QuestionCard(
                    q_id, sub, dif, year_label, q_type, card_html, is_checked, self.toggle_question_selection,
                    question_source=question_source, source_year=question_source_year,
                    result_viewport=self.scroll_area.viewport(),
                    edit_callback=lambda question_id: self.open_question_for_edit(question_id, False),
                    duplicate_callback=lambda question_id: self.open_question_for_edit(question_id, True),
                    last_modified=row[15]
                )
                card.checkbox.setStyle(self._selection_style)
                cards.append(card)

            while self.scroll_layout.count():
                widget = self.scroll_layout.takeAt(0).widget()
                if widget:
                    dispose_question_card(widget)
            for card in cards:
                self.scroll_layout.addWidget(card)
            self.search_view.page = bounds.page or 1
            self.lbl_result_range.setText(
                f"Mostrando {bounds.start}–{bounds.end} de {bounds.total} questões"
                if bounds.total else "Nenhuma questão encontrada (0 questões)")
            self.lbl_page_count.setText(f"Página {bounds.page} de {bounds.pages}")
            self.page_selector.blockSignals(True)
            self.page_selector.setRange(1, max(1, bounds.pages))
            self.page_selector.setValue(bounds.page or 1)
            self.page_selector.blockSignals(False)
            self.page_selector.setEnabled(bounds.pages > 0)
            self.btn_previous_page.setEnabled(bounds.page > 1)
            self.btn_next_page.setEnabled(bounds.page < bounds.pages)
            return True
        except Exception as e:
            for card in cards:
                dispose_question_card(card)
            self.show_alert("Erro", f"Erro ao buscar questões:\n{str(e)}", QMessageBox.Warning)
            return False

    def current_search_filters(self, bounds=None):
        if bounds is None:
            bounds = validate_year_range(self.txt_search_source_year_from.text(), self.txt_search_source_year_to.text())
        return SearchFilters(
            difficulties=tuple(self.checked_filter_values(self.search_diff_group, "Todas as Dificuldades")),
            question_types=tuple(self.checked_filter_values(self.search_type_group, "Todos os Tipos")),
            text=self.txt_search_question_text.text().strip(),
            source=self.txt_search_question_source.text().strip(),
            source_year_from=bounds[0], source_year_to=bounds[1],
            school_years=tuple(self.checked_filter_values(self.search_year_group, "Todos os Anos")),
            categories=tuple(self.get_checked_subjects(self.tree_search_subjects)),
        )

    def toggle_selected_question_view(self, checked):
        previous_mode, previous_page = self.search_view.selected_only, self.search_view.page
        if not self.search_view.set_selected_only(checked):
            self.btn_browse_selected_questions.blockSignals(True)
            self.btn_browse_selected_questions.setChecked(False)
            self.btn_browse_selected_questions.blockSignals(False)
            return
        if not self.load_questions(selected_only=checked):
            self.search_view.selected_only, self.search_view.page = previous_mode, previous_page
            self.btn_browse_selected_questions.blockSignals(True)
            self.btn_browse_selected_questions.setChecked(previous_mode)
            self.btn_browse_selected_questions.blockSignals(False)
            return
        self.btn_browse_selected_questions.setText(
            "Navegando pelas questões selecionadas" if checked else "Navegar pelas questões selecionadas")
        self.btn_browse_selected_questions.setEnabled(bool(self.selected_ids) or checked)
        self.scroll_area.verticalScrollBar().setValue(0)

    def show_filtered_questions(self):
        try:
            filters = self.current_search_filters()
        except YearRangeError as e:
            message = ("O ano em 'Desde' deve ser menor ou igual ao ano em 'até'."
                       if e.code == 'inverted' else
                       "Informe um ano inteiro entre 1 e 9999 ou deixe o campo vazio.")
            self.show_alert("Ano da fonte inválido", message, QMessageBox.Warning)
            (self.txt_search_source_year_from if e.field == 'from' else self.txt_search_source_year_to).setFocus()
            return
        previous = (self.search_view.applied, self.search_view.selected_only, self.search_view.page)
        self.search_view.apply(filters)
        if not self.load_questions():
            self.search_view.applied, self.search_view.selected_only, self.search_view.page = previous
            return
        self.btn_browse_selected_questions.blockSignals(True)
        self.btn_browse_selected_questions.setChecked(False)
        self.btn_browse_selected_questions.blockSignals(False)
        self.btn_browse_selected_questions.setText("Navegar pelas questões selecionadas")
        self.btn_browse_selected_questions.setEnabled(bool(self.selected_ids))
        self.scroll_area.verticalScrollBar().setValue(0)

    def toggle_question_selection(self, q_id, state):
        if state == Qt.Checked.value or state == 2:
            self.selected_ids.add(q_id)
        else:
            self.selected_ids.discard(q_id)
            self.exam_order.synchronize(self.selected_ids)
        self.lbl_selected_count.setText(f"{len(self.selected_ids)} questão(ões) selecionada(s) para a prova")
        self.btn_delete_selected_questions.setEnabled(bool(self.selected_ids))
        selected_view = self.btn_browse_selected_questions.isChecked()
        self.btn_browse_selected_questions.setEnabled(bool(self.selected_ids) or selected_view)
        self.update_multi_version_controls()
        if selected_view:
            self.load_questions(selected_only=True)

    def delete_selected_questions(self):
        if not self.conn:
            self.show_alert("Erro", "O banco de dados não está conectado.", QMessageBox.Critical)
            return
        if not self.selected_ids:
            self.show_alert("Aviso", "Selecione ao menos uma questão para excluir.", QMessageBox.Warning)
            return

        question_ids = set(self.selected_ids)
        count = len(question_ids)
        database_name = os.path.splitext(os.path.basename(self.db_path))[0] or self.current_discipline
        if not self.show_confirm(
            "Confirmar exclusão de questões",
            f"Banco de dados: {database_name}\nQuestões selecionadas: {count}\n\n"
            "Tem certeza de que deseja excluí-las permanentemente? Esta ação não pode ser desfeita."
        ):
            return

        try:
            placeholders = ",".join("?" for _ in question_ids)
            cursor = self.conn.cursor()
            cursor.execute(f"DELETE FROM questoes WHERE id IN ({placeholders})", list(question_ids))
            deleted_count = cursor.rowcount
            self.conn.commit()
            self.selected_ids.difference_update(question_ids)
            self.exam_order.synchronize(self.selected_ids)
            self.lbl_selected_count.setText(f"{len(self.selected_ids)} questão(ões) selecionada(s) para a prova")
            self.btn_delete_selected_questions.setEnabled(bool(self.selected_ids))
            selected_view = self.btn_browse_selected_questions.isChecked()
            self.btn_browse_selected_questions.setEnabled(bool(self.selected_ids) or selected_view)
            self.update_multi_version_controls()
            self.load_questions(selected_only=selected_view)
            self.show_alert("Exclusão concluída", f"{deleted_count} questão(ões) excluída(s) do banco de dados.", QMessageBox.Information)
        except Exception as e:
            self.conn.rollback()
            self.show_alert("Erro", f"Falha ao excluir as questões:\n{str(e)}", QMessageBox.Critical)

    # --- TAB 3: EXAM CONFIGURE & DOCX PARSER ENGINE ---
    def setup_tab_generate(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        content = QWidget()
        content.setMaximumWidth(880)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(18)
        
        lbl_title = QLabel("Configurar e Gerar Arquivo Word (.docx)")
        lbl_title.setObjectName("HeaderLabel")
        content_layout.addWidget(lbl_title)

        config_frame = QFrame()
        config_frame.setObjectName("GenerationOptionsPanel")
        config_layout = QVBoxLayout(config_frame)
        config_layout.setContentsMargins(24, 20, 24, 20)
        config_layout.setSpacing(14)

        def add_generation_divider():
            divider = QFrame()
            divider.setObjectName("FilterSectionDivider")
            config_layout.addWidget(divider)

        options_title = QLabel("Opções da prova")
        options_title.setObjectName("FilterHeaderLabel")
        options_title.setAlignment(Qt.AlignCenter)
        config_layout.addWidget(options_title)

        self.chk_multiple_versions = QCheckBox("Gerar múltiplas versões")
        self.chk_multiple_versions.toggled.connect(self.update_multi_version_controls)
        config_layout.addWidget(self.chk_multiple_versions)

        version_row = QHBoxLayout()
        self.lbl_version_count = QLabel("Número de versões:")
        version_row.addWidget(self.lbl_version_count)
        self.spin_version_count = InterfaceSpinBox()
        self.spin_version_count.setButtonSymbols(QSpinBox.UpDownArrows)
        self.spin_version_count.setRange(2, 999)
        self.spin_version_count.setValue(2)
        self.spin_version_count.setFixedWidth(100)
        self.spin_version_count.setAlignment(Qt.AlignCenter)
        version_row.addWidget(self.spin_version_count)
        version_row.addStretch()
        config_layout.addLayout(version_row)
        add_generation_divider()

        randomization_row = QHBoxLayout()
        self.chk_shuffle_questions = QCheckBox("Embaralhar questões")
        randomization_row.addWidget(self.chk_shuffle_questions)
        self.chk_shuffle_alternatives = QCheckBox("Embaralhar alternativas")
        randomization_row.addWidget(self.chk_shuffle_alternatives)
        randomization_row.addStretch()
        config_layout.addLayout(randomization_row)
        add_generation_divider()
        self.update_multi_version_controls(False)
        
        self.chk_include_answers = QCheckBox("Incluir gabarito oficial em página separada no final do documento?")
        self.chk_include_answers.setChecked(True)
        config_layout.addWidget(self.chk_include_answers)
        self.chk_separate_answers = QCheckBox("Gabarito em arquivo separado")
        self.chk_include_answers.toggled.connect(self.chk_separate_answers.setEnabled)
        config_layout.addWidget(self.chk_separate_answers)
        add_generation_divider()
        order_label = QLabel("Ordem das questões selecionadas:")
        config_layout.addWidget(order_label)
        self.list_exam_order = QListWidget()
        self.list_exam_order.setMinimumHeight(100)
        self.list_exam_order.setMaximumHeight(180)
        config_layout.addWidget(self.list_exam_order)
        order_buttons = QHBoxLayout()
        self.btn_order_up = QPushButton("Subir")
        self.btn_order_up.clicked.connect(lambda: self.move_exam_question(-1))
        self.btn_order_down = QPushButton("Descer")
        self.btn_order_down.clicked.connect(lambda: self.move_exam_question(1))
        order_buttons.addWidget(self.btn_order_up); order_buttons.addWidget(self.btn_order_down)
        order_buttons.addStretch()
        config_layout.addLayout(order_buttons)

        content_layout.addWidget(config_frame)

        btn_generate = QPushButton("Gerar Arquivo da Prova")
        btn_generate.setObjectName("PrimaryButton")
        btn_generate.setFixedSize(360, 38 if IS_WINDOWS else 54)
        btn_generate.clicked.connect(self.generate_word_doc)
        self.btn_generate = btn_generate

        generate_row = QHBoxLayout()
        generate_row.addStretch()
        generate_row.addWidget(btn_generate)
        generate_row.addStretch()
        content_layout.addLayout(generate_row)

        generation_scroll = QScrollArea()
        generation_scroll.setWidgetResizable(True)
        generation_scroll.setWidget(content)
        layout.addWidget(generation_scroll)
        self.tabs.addTab(tab, "Configurar e Gerar Prova")

    def update_multi_version_controls(self, *_):
        enabled = self.chk_multiple_versions.isChecked()
        self.lbl_version_count.setEnabled(enabled)
        self.spin_version_count.setEnabled(enabled)
        self.chk_shuffle_questions.setEnabled(enabled)
        self.chk_shuffle_alternatives.setEnabled(enabled)
        if not enabled:
            self.chk_shuffle_alternatives.setToolTip("Ative 'Gerar múltiplas versões' para habilitar esta opção.")
        else:
            self.chk_shuffle_alternatives.setToolTip("Reordena as alternativas das questões de múltipla escolha.")

    @staticmethod
    def make_version_questions(source_questions, shuffle_questions, shuffle_alternatives):
        return make_version_questions(source_questions, shuffle_questions, shuffle_alternatives)

    def on_exam_tab_changed(self, index):
        if index == 2:
            self.refresh_exam_order()

    def refresh_exam_order(self):
        ids = self.exam_order.synchronize(self.selected_ids)
        try:
            summaries = fetch_question_summaries(self.conn, ids) if self.conn and ids else {}
        except Exception as e:
            self.show_alert("Erro", f"Não foi possível carregar as questões selecionadas: {e}", QMessageBox.Warning)
            return
        self.list_exam_order.clear()
        for question_id in ids:
            summary = summaries.get(question_id, '')
            self.list_exam_order.addItem(f"Questão {question_id}" + (f" — {summary}" if summary else ""))
        if ids:
            self.list_exam_order.setCurrentRow(0)

    def move_exam_question(self, delta):
        row = self.list_exam_order.currentRow()
        target = self.exam_order.move(row, delta)
        if target != row:
            item = self.list_exam_order.takeItem(row)
            self.list_exam_order.insertItem(target, item)
            self.list_exam_order.setCurrentRow(target)

    def build_exam_document(self, questions):
        placement = 'end' if self.chk_include_answers.isChecked() else 'none'
        return build_exam_documents(questions, answer_placement=placement)[0]

    def generate_word_doc(self):
        if not self.selected_ids:
            self.show_alert("Aviso", "Nenhuma questão selecionada! Vá para a aba de busca e selecione questões primeiro.", QMessageBox.Warning)
            return
        self.btn_generate.setEnabled(False)
        targets = []
        try:
            ordered_ids = self.exam_order.synchronize(self.selected_ids)
            questions = fetch_ordered_questions(self.conn, ordered_ids)
            multiple = self.chk_multiple_versions.isChecked()
            count = self.spin_version_count.value() if multiple else 1
            placement = ('none' if not self.chk_include_answers.isChecked() else
                         'separate' if self.chk_separate_answers.isChecked() else 'end')
            versions = generate_versions(questions, count,
                multiple and self.chk_shuffle_questions.isChecked(),
                multiple and self.chk_shuffle_alternatives.isChecked())
            issues = inspect_question_images(questions, include_answers=placement != 'none')
            acknowledged = set()
            if issues:
                details = sorted({(issue.question_id, issue.reason) for issue in issues})
                message = "Algumas imagens não podem ser exportadas:\n\n" + "\n".join(
                    f"Questão {question_id}: {reason}" for question_id, reason in details)
                if not self.show_confirm("Imagens não exportáveis", message + "\n\nContinuar sem essas imagens?"):
                    return
                acknowledged = {(issue.question_id, issue.source) for issue in issues}
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Salvar Prova", f"Prova_{self.current_discipline}.docx", "Word Document (*.docx)")
            if not file_path:
                return
            paths = output_paths(file_path, count, placement)
            targets = [path for pair in paths for path in pair if path is not None]
            existing = [path for path in targets if path.exists()]
            if existing and not self.show_confirm("Confirmar substituição de arquivos",
                    "Os arquivos a seguir já existem e serão substituídos:\n\n" + "\n".join(map(str, existing))):
                return
            def documents():
                rendered_versions = set()
                for number, (version, pair) in enumerate(zip(versions, paths), start=1):
                    exam, answer = build_exam_documents(version,
                        version_number=number if multiple else None,
                        answer_placement=placement, acknowledged_images=acknowledged)
                    if multiple and (self.chk_shuffle_questions.isChecked() or self.chk_shuffle_alternatives.isChecked()):
                        signature = exam_content_fingerprint(exam, version_number=number)
                        if signature in rendered_versions:
                            raise ValueError("Não foi possível gerar versões visualmente distintas com as opções escolhidas.")
                        rendered_versions.add(signature)
                    yield pair[0], exam
                    if answer is not None:
                        yield pair[1], answer
            written = publish_documents(documents(), confirmed=existing)
            self.show_alert("Sucesso", "Arquivos salvos:\n" + "\n".join(map(str, written)), QMessageBox.Information)
        except PublicationError as e:
            message = f"Não foi possível concluir a geração: {e}"
            if e.published:
                message += "\n\nArquivos salvos:\n" + "\n".join(map(str, e.published))
                missing = [path for path in targets if path not in e.published]
                if missing:
                    message += "\n\nArquivos não salvos:\n" + "\n".join(map(str, missing))
            self.show_alert("Erro ao gerar documentos", message, QMessageBox.Warning)
        except Exception as e:
            self.show_alert("Erro ao gerar documentos", f"Não foi possível gerar a prova: {e}", QMessageBox.Critical)
        finally:
            self.btn_generate.setEnabled(True)
