#!/usr/bin/env python3
"""
AI Chat Room - Full Android Application with Complete GUI

A comprehensive Kivy-based Android application for the AI Chat Room.
Provides a complete native Android experience with:
- Multi-AI conversations with 10 personalities
- Private chat between any participants (AI-to-AI, User-to-AI)
- Document upload and analysis
- AI participant management (add/remove/rename)
- Tool use
- Add-on/plugin system
- P2P networking
- Persistent state storage
- Full settings management
- Local Gemma 3 4B model (Pixel TPU optimized)

This file is the main entry point for the Android app.
"""

import os
import sys
# random already imported at top
from datetime import datetime
from typing import Dict, List, Optional, Any

# Ensure the app directory is in the path
app_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, app_dir)
sys.path.insert(0, os.path.join(app_dir, '..', 'src'))

# Kivy configuration (must be before importing kivy)
os.environ['KIVY_LOG_LEVEL'] = 'info'

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.modalview import ModalView
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.recycleview import RecycleView
from kivy.uix.spinner import Spinner
from kivy.uix.slider import Slider
from kivy.uix.switch import Switch
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.actionbar import ActionBar, ActionView, ActionButton, ActionPrevious
from kivy.properties import (
    StringProperty, ListProperty, BooleanProperty, 
    NumericProperty, ObjectProperty, DictProperty
)
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.animation import Animation
from kivy.utils import get_color_from_hex

# Import app modules
try:
    from addons import addon_manager, get_addon_manager
except ImportError:
    addon_manager = None
    def get_addon_manager():
        return None

try:
    from ai_state import get_state_manager, AIState, EmotionalState
except ImportError:
    def get_state_manager():
        return None
    AIState = None
    EmotionalState = None

try:
    from personalities import BUILTIN_PERSONALITIES, PersonalityDefinition
except ImportError:
    BUILTIN_PERSONALITIES = []
    PersonalityDefinition = None

try:
    from model_manager import get_model_manager, MODEL_CATALOG, ModelInfo, ModelSize
except ImportError:
    def get_model_manager():
        return None
    MODEL_CATALOG = {}
    ModelInfo = None
    ModelSize = None

# Color scheme
COLORS = {
    'primary': '#6200EE',
    'primary_dark': '#3700B3',
    'secondary': '#03DAC6',
    'background': '#121212',
    'surface': '#1E1E1E',
    'error': '#CF6679',
    'on_primary': '#FFFFFF',
    'on_background': '#FFFFFF',
    'on_surface': '#FFFFFF',
    'text_secondary': '#B3B3B3',
    'divider': '#2D2D2D',
    'ai_message': '#2D2D3D',
    'user_message': '#1A472A',
    'private_message': '#3D2D2D',
    'system_message': '#2D3D2D',
}

# Default AI personalities for the app
DEFAULT_PERSONALITIES = [
    {"id": "nova", "name": "Nova", "avatar": "🌟", "personality": "Curious and analytical", "color": "#FFD700"},
    {"id": "echo", "name": "Echo", "avatar": "🎭", "personality": "Creative and playful", "color": "#FF69B4"},
    {"id": "sage", "name": "Sage", "avatar": "🦉", "personality": "Wise and contemplative", "color": "#4169E1"},
    {"id": "spark", "name": "Spark", "avatar": "⚡", "personality": "Energetic and enthusiastic", "color": "#FF4500"},
    {"id": "atlas", "name": "Atlas", "avatar": "🗺️", "personality": "Practical and structured", "color": "#2E8B57"},
    {"id": "luna", "name": "Luna", "avatar": "🌙", "personality": "Empathetic and nurturing", "color": "#9370DB"},
    {"id": "cipher", "name": "Cipher", "avatar": "🔮", "personality": "Logical and precise", "color": "#00CED1"},
    {"id": "muse", "name": "Muse", "avatar": "🎨", "personality": "Artistic and inspiring", "color": "#FF1493"},
    {"id": "phoenix", "name": "Phoenix", "avatar": "🔥", "personality": "Resilient and transformative", "color": "#FF6347"},
    {"id": "zen", "name": "Zen", "avatar": "☯️", "personality": "Calm and mindful", "color": "#98FB98"},
]


# Kivy UI definition - Comprehensive GUI
KV = '''
#:import utils kivy.utils
#:import dp kivy.metrics.dp
#:import sp kivy.metrics.sp
#:import Clock kivy.clock.Clock
#:import Animation kivy.animation.Animation

# ============================================
# Custom Widgets
# ============================================

<RoundedButton@Button>:
    background_color: 0, 0, 0, 0
    background_normal: ''
    canvas.before:
        Color:
            rgba: utils.get_color_from_hex('#6200EE') if self.state == 'normal' else utils.get_color_from_hex('#3700B3')
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(10)]

<IconButton@Button>:
    size_hint: None, None
    size: dp(48), dp(48)
    background_color: 0, 0, 0, 0
    background_normal: ''
    font_size: sp(24)

<ChatBubble>:
    size_hint_y: None
    height: self.minimum_height
    padding: dp(8), dp(4)
    
    canvas.before:
        Color:
            rgba: self.bubble_color
        RoundedRectangle:
            pos: self.x + dp(4), self.y + dp(2)
            size: self.width - dp(8), self.height - dp(4)
            radius: [dp(12), dp(12), dp(12), dp(4)] if self.is_user else [dp(12), dp(12), dp(4), dp(12)]
    
    BoxLayout:
        orientation: 'vertical'
        size_hint_y: None
        height: self.minimum_height
        padding: dp(12)
        spacing: dp(4)
        
        BoxLayout:
            size_hint_y: None
            height: dp(24)
            spacing: dp(8)
            
            Label:
                text: root.avatar + ' ' + root.sender
                size_hint_x: None
                width: self.texture_size[0]
                font_size: sp(13)
                bold: True
                color: root.sender_color
            
            Label:
                text: root.timestamp
                font_size: sp(10)
                color: 0.6, 0.6, 0.6, 1
                halign: 'right'
                text_size: self.size
        
        Label:
            text: root.content
            size_hint_y: None
            height: self.texture_size[1]
            text_size: self.width, None
            halign: 'left'
            valign: 'top'
            font_size: sp(14)
            markup: True
            color: 1, 1, 1, 0.95

<AIParticipantCard>:
    size_hint_y: None
    height: dp(80)
    padding: dp(12)
    spacing: dp(12)
    
    canvas.before:
        Color:
            rgba: utils.get_color_from_hex('#2D2D2D') if not root.is_selected else utils.get_color_from_hex('#3D3D5D')
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(12)]
    
    Label:
        text: root.avatar
        size_hint_x: None
        width: dp(48)
        font_size: sp(32)
    
    BoxLayout:
        orientation: 'vertical'
        spacing: dp(4)
        
        BoxLayout:
            size_hint_y: None
            height: dp(24)
            
            Label:
                text: root.display_name
                font_size: sp(16)
                bold: True
                halign: 'left'
                text_size: self.size
                color: utils.get_color_from_hex(root.ai_color)
            
            Label:
                text: root.emotion_emoji
                size_hint_x: None
                width: dp(30)
                font_size: sp(16)
        
        Label:
            text: root.personality[:50] + '...' if len(root.personality) > 50 else root.personality
            font_size: sp(12)
            color: 0.7, 0.7, 0.7, 1
            halign: 'left'
            text_size: self.size
    
    Switch:
        id: active_switch
        size_hint_x: None
        width: dp(50)
        active: root.is_active
        on_active: root.toggle_active(self.active)

<PrivateChatItem>:
    size_hint_y: None
    height: dp(70)
    padding: dp(12)
    spacing: dp(12)
    
    canvas.before:
        Color:
            rgba: utils.get_color_from_hex('#2D2D2D')
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(12)]
    
    Label:
        text: root.participant_avatar
        size_hint_x: None
        width: dp(48)
        font_size: sp(28)
    
    BoxLayout:
        orientation: 'vertical'
        spacing: dp(2)
        
        Label:
            text: root.participant_name
            font_size: sp(15)
            bold: True
            halign: 'left'
            text_size: self.size
        
        Label:
            text: root.last_message[:40] + '...' if len(root.last_message) > 40 else root.last_message
            font_size: sp(12)
            color: 0.6, 0.6, 0.6, 1
            halign: 'left'
            text_size: self.size
    
    Label:
        text: root.timestamp
        size_hint_x: None
        width: dp(50)
        font_size: sp(10)
        color: 0.5, 0.5, 0.5, 1

<DocumentCard>:
    size_hint_y: None
    height: dp(70)
    padding: dp(12)
    spacing: dp(12)
    
    canvas.before:
        Color:
            rgba: utils.get_color_from_hex('#2D3D2D')
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(12)]
    
    Label:
        text: '📄'
        size_hint_x: None
        width: dp(40)
        font_size: sp(24)
    
    BoxLayout:
        orientation: 'vertical'
        
        Label:
            text: root.doc_name
            font_size: sp(14)
            bold: True
            halign: 'left'
            text_size: self.size
        
        Label:
            text: root.doc_info
            font_size: sp(11)
            color: 0.6, 0.6, 0.6, 1
            halign: 'left'
            text_size: self.size
    
    IconButton:
        text: '✕'
        on_release: root.remove_document()

<ToolCard>:
    size_hint_y: None
    height: dp(60)
    padding: dp(10)
    spacing: dp(10)
    
    canvas.before:
        Color:
            rgba: utils.get_color_from_hex('#2D2D3D')
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(8)]
    
    Label:
        text: root.tool_icon
        size_hint_x: None
        width: dp(36)
        font_size: sp(20)
    
    BoxLayout:
        orientation: 'vertical'
        
        Label:
            text: root.tool_name
            font_size: sp(13)
            bold: True
            halign: 'left'
            text_size: self.size
        
        Label:
            text: root.tool_desc
            font_size: sp(10)
            color: 0.6, 0.6, 0.6, 1
            halign: 'left'
            text_size: self.size
            shorten: True
            shorten_from: 'right'

# ============================================
# Screens
# ============================================

<MainChatScreen>:
    name: 'main_chat'
    
    BoxLayout:
        orientation: 'vertical'
        
        # Top Bar
        BoxLayout:
            size_hint_y: None
            height: dp(56)
            padding: dp(8)
            spacing: dp(8)
            
            canvas.before:
                Color:
                    rgba: utils.get_color_from_hex('#1E1E1E')
                Rectangle:
                    pos: self.pos
                    size: self.size
            
            IconButton:
                text: '☰'
                on_release: app.toggle_drawer()
            
            Label:
                text: 'AI Chat Room'
                font_size: sp(18)
                bold: True
                halign: 'left'
                text_size: self.size
            
            Label:
                id: connection_status
                text: '🟢 Local'
                size_hint_x: None
                width: dp(70)
                font_size: sp(12)
                color: 0.6, 0.6, 0.6, 1
            
            IconButton:
                text: '👥'
                on_release: app.show_participants()
            
            IconButton:
                text: '⚙️'
                on_release: app.show_settings()
        
        # Active AIs Bar
        ScrollView:
            size_hint_y: None
            height: dp(60)
            do_scroll_y: False
            
            BoxLayout:
                id: active_ais_bar
                size_hint_x: None
                width: self.minimum_width
                padding: dp(8)
                spacing: dp(8)
        
        # Chat Area
        BoxLayout:
            orientation: 'vertical'
            
            # Private chat indicator
            BoxLayout:
                id: private_chat_bar
                size_hint_y: None
                height: dp(0)
                opacity: 0
                padding: dp(8)
                
                canvas.before:
                    Color:
                        rgba: utils.get_color_from_hex('#3D2D2D')
                    Rectangle:
                        pos: self.pos
                        size: self.size
                
                Label:
                    id: private_chat_label
                    text: '🔒 Private chat with Nova'
                    font_size: sp(13)
                    halign: 'left'
                    text_size: self.size
                
                Button:
                    text: 'End'
                    size_hint_x: None
                    width: dp(60)
                    on_release: app.end_private_chat()
            
            # Chat Messages
            ScrollView:
                id: chat_scroll
                do_scroll_x: False
                bar_width: dp(4)
                
                BoxLayout:
                    id: chat_history
                    orientation: 'vertical'
                    size_hint_y: None
                    height: self.minimum_height
                    padding: dp(8)
                    spacing: dp(8)
            
            # Document indicator
            BoxLayout:
                id: document_bar
                size_hint_y: None
                height: dp(0)
                opacity: 0
                padding: dp(8)
                
                canvas.before:
                    Color:
                        rgba: utils.get_color_from_hex('#2D3D2D')
                    Rectangle:
                        pos: self.pos
                        size: self.size
                
                Label:
                    text: '📄'
                    size_hint_x: None
                    width: dp(30)
                
                Label:
                    id: document_label
                    text: 'document.txt'
                    font_size: sp(12)
                    halign: 'left'
                    text_size: self.size
                
                Button:
                    text: '✕'
                    size_hint_x: None
                    width: dp(40)
                    on_release: app.clear_document()
        
        # Input Area
        BoxLayout:
            size_hint_y: None
            height: dp(60)
            padding: dp(8)
            spacing: dp(8)
            
            canvas.before:
                Color:
                    rgba: utils.get_color_from_hex('#1E1E1E')
                Rectangle:
                    pos: self.pos
                    size: self.size
            
            IconButton:
                text: '📎'
                on_release: app.show_attachment_menu()
            
            TextInput:
                id: message_input
                hint_text: 'Type a message...'
                multiline: False
                background_color: utils.get_color_from_hex('#2D2D2D')
                foreground_color: 1, 1, 1, 1
                hint_text_color: 0.5, 0.5, 0.5, 1
                cursor_color: utils.get_color_from_hex('#6200EE')
                padding: dp(12)
                on_text_validate: app.send_message()
            
            IconButton:
                text: '🎤'
                on_release: app.start_voice_input()
            
            RoundedButton:
                text: '➤'
                size_hint_x: None
                width: dp(48)
                font_size: sp(20)
                on_release: app.send_message()

<ParticipantsScreen>:
    name: 'participants'
    
    BoxLayout:
        orientation: 'vertical'
        
        # Header
        BoxLayout:
            size_hint_y: None
            height: dp(56)
            padding: dp(8)
            spacing: dp(8)
            
            canvas.before:
                Color:
                    rgba: utils.get_color_from_hex('#1E1E1E')
                Rectangle:
                    pos: self.pos
                    size: self.size
            
            IconButton:
                text: '←'
                on_release: app.go_to_chat()
            
            Label:
                text: 'AI Participants'
                font_size: sp(18)
                bold: True
                halign: 'left'
                text_size: self.size
            
            IconButton:
                text: '+'
                on_release: app.show_add_ai_dialog()
        
        # Tabs
        TabbedPanel:
            do_default_tab: False
            tab_height: dp(48)
            
            TabbedPanelItem:
                text: 'Active'
                
                ScrollView:
                    BoxLayout:
                        id: active_participants_list
                        orientation: 'vertical'
                        size_hint_y: None
                        height: self.minimum_height
                        padding: dp(12)
                        spacing: dp(8)
            
            TabbedPanelItem:
                text: 'All'
                
                ScrollView:
                    BoxLayout:
                        id: all_participants_list
                        orientation: 'vertical'
                        size_hint_y: None
                        height: self.minimum_height
                        padding: dp(12)
                        spacing: dp(8)
            
            TabbedPanelItem:
                text: 'Private Chats'
                
                ScrollView:
                    BoxLayout:
                        id: private_chats_list
                        orientation: 'vertical'
                        size_hint_y: None
                        height: self.minimum_height
                        padding: dp(12)
                        spacing: dp(8)

<SettingsScreen>:
    name: 'settings'
    
    BoxLayout:
        orientation: 'vertical'
        
        # Header
        BoxLayout:
            size_hint_y: None
            height: dp(56)
            padding: dp(8)
            spacing: dp(8)
            
            canvas.before:
                Color:
                    rgba: utils.get_color_from_hex('#1E1E1E')
                Rectangle:
                    pos: self.pos
                    size: self.size
            
            IconButton:
                text: '←'
                on_release: app.go_to_chat()
            
            Label:
                text: 'Settings'
                font_size: sp(18)
                bold: True
                halign: 'left'
                text_size: self.size
        
        ScrollView:
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                padding: dp(16)
                spacing: dp(16)
                
                # User Profile Section
                Label:
                    text: 'Profile'
                    font_size: sp(14)
                    bold: True
                    color: utils.get_color_from_hex('#6200EE')
                    size_hint_y: None
                    height: dp(30)
                    halign: 'left'
                    text_size: self.size
                
                BoxLayout:
                    size_hint_y: None
                    height: dp(50)
                    spacing: dp(12)
                    
                    Label:
                        text: 'Your Name'
                        size_hint_x: 0.35
                        halign: 'left'
                        text_size: self.size
                    
                    TextInput:
                        id: user_name_input
                        text: 'User'
                        hint_text: 'Enter your name'
                        multiline: False
                        size_hint_x: 0.65
                        background_color: utils.get_color_from_hex('#2D2D2D')
                        foreground_color: 1, 1, 1, 1
                        padding: dp(12)
                
                # Model Settings Section
                Label:
                    text: 'AI Model'
                    font_size: sp(14)
                    bold: True
                    color: utils.get_color_from_hex('#6200EE')
                    size_hint_y: None
                    height: dp(30)
                    halign: 'left'
                    text_size: self.size
                
                BoxLayout:
                    size_hint_y: None
                    height: dp(50)
                    spacing: dp(12)
                    
                    Label:
                        text: 'Model'
                        size_hint_x: 0.35
                        halign: 'left'
                        text_size: self.size
                    
                    Spinner:
                        id: model_spinner
                        text: 'ollama/gemma3:4b'
                        values: ['ollama/gemma3:4b', 'ollama/gemma3:2b', 'ollama/llama3:8b', 'gemini/gemini-2.0-flash']
                        size_hint_x: 0.65
                        background_color: utils.get_color_from_hex('#2D2D2D')
                
                BoxLayout:
                    size_hint_y: None
                    height: dp(50)
                    spacing: dp(12)
                    
                    Label:
                        text: 'Ollama URL'
                        size_hint_x: 0.35
                        halign: 'left'
                        text_size: self.size
                    
                    TextInput:
                        id: ollama_url_input
                        text: 'http://localhost:11434'
                        multiline: False
                        size_hint_x: 0.65
                        background_color: utils.get_color_from_hex('#2D2D2D')
                        foreground_color: 1, 1, 1, 1
                        padding: dp(12)
                
                BoxLayout:
                    size_hint_y: None
                    height: dp(50)
                    spacing: dp(12)
                    
                    Label:
                        text: 'API Key'
                        size_hint_x: 0.35
                        halign: 'left'
                        text_size: self.size
                    
                    TextInput:
                        id: api_key_input
                        hint_text: 'For cloud models only'
                        password: True
                        multiline: False
                        size_hint_x: 0.65
                        background_color: utils.get_color_from_hex('#2D2D2D')
                        foreground_color: 1, 1, 1, 1
                        padding: dp(12)
                
                # P2P Settings
                Label:
                    text: 'P2P Networking'
                    font_size: sp(14)
                    bold: True
                    color: utils.get_color_from_hex('#6200EE')
                    size_hint_y: None
                    height: dp(30)
                    halign: 'left'
                    text_size: self.size
                
                BoxLayout:
                    size_hint_y: None
                    height: dp(50)
                    spacing: dp(12)
                    
                    Label:
                        text: 'Enable P2P'
                        size_hint_x: 0.7
                        halign: 'left'
                        text_size: self.size
                    
                    Switch:
                        id: p2p_switch
                        size_hint_x: 0.3
                
                RoundedButton:
                    text: 'Host Room'
                    size_hint_y: None
                    height: dp(48)
                    on_release: app.host_room()
                
                BoxLayout:
                    size_hint_y: None
                    height: dp(50)
                    spacing: dp(8)
                    
                    TextInput:
                        id: join_code_input
                        hint_text: 'Enter share code'
                        multiline: False
                        background_color: utils.get_color_from_hex('#2D2D2D')
                        foreground_color: 1, 1, 1, 1
                        padding: dp(12)
                    
                    RoundedButton:
                        text: 'Join'
                        size_hint_x: None
                        width: dp(80)
                        on_release: app.join_room()
                
                # Storage
                Label:
                    text: 'Data Storage'
                    font_size: sp(14)
                    bold: True
                    color: utils.get_color_from_hex('#6200EE')
                    size_hint_y: None
                    height: dp(30)
                    halign: 'left'
                    text_size: self.size
                
                Label:
                    id: storage_path_label
                    text: 'Storage: ~/Documents/AIChat'
                    font_size: sp(12)
                    color: 0.6, 0.6, 0.6, 1
                    size_hint_y: None
                    height: dp(30)
                    halign: 'left'
                    text_size: self.size
                
                BoxLayout:
                    size_hint_y: None
                    height: dp(48)
                    spacing: dp(12)
                    
                    RoundedButton:
                        text: 'Export Data'
                        on_release: app.export_data()
                    
                    RoundedButton:
                        text: 'Import Data'
                        on_release: app.import_data()
                
                # Save Button
                Widget:
                    size_hint_y: None
                    height: dp(20)
                
                RoundedButton:
                    text: 'Save Settings'
                    size_hint_y: None
                    height: dp(52)
                    on_release: app.save_settings()

<DocumentsScreen>:
    name: 'documents'
    
    BoxLayout:
        orientation: 'vertical'
        
        # Header
        BoxLayout:
            size_hint_y: None
            height: dp(56)
            padding: dp(8)
            spacing: dp(8)
            
            canvas.before:
                Color:
                    rgba: utils.get_color_from_hex('#1E1E1E')
                Rectangle:
                    pos: self.pos
                    size: self.size
            
            IconButton:
                text: '←'
                on_release: app.go_to_chat()
            
            Label:
                text: 'Documents'
                font_size: sp(18)
                bold: True
                halign: 'left'
                text_size: self.size
            
            IconButton:
                text: '+'
                on_release: app.show_file_chooser()
        
        ScrollView:
            BoxLayout:
                id: documents_list
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                padding: dp(12)
                spacing: dp(8)

<ToolsScreen>:
    name: 'tools'
    
    BoxLayout:
        orientation: 'vertical'
        
        # Header
        BoxLayout:
            size_hint_y: None
            height: dp(56)
            padding: dp(8)
            spacing: dp(8)
            
            canvas.before:
                Color:
                    rgba: utils.get_color_from_hex('#1E1E1E')
                Rectangle:
                    pos: self.pos
                    size: self.size
            
            IconButton:
                text: '←'
                on_release: app.go_to_chat()
            
            Label:
                text: 'Tools'
                font_size: sp(18)
                bold: True
                halign: 'left'
                text_size: self.size
        
        ScrollView:
            BoxLayout:
                id: tools_list
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                padding: dp(12)
                spacing: dp(8)

<AddonsScreen>:
    name: 'addons'
    
    BoxLayout:
        orientation: 'vertical'
        
        # Header
        BoxLayout:
            size_hint_y: None
            height: dp(56)
            padding: dp(8)
            spacing: dp(8)
            
            canvas.before:
                Color:
                    rgba: utils.get_color_from_hex('#1E1E1E')
                Rectangle:
                    pos: self.pos
                    size: self.size
            
            IconButton:
                text: '←'
                on_release: app.go_to_chat()
            
            Label:
                text: 'Add-ons'
                font_size: sp(18)
                bold: True
                halign: 'left'
                text_size: self.size
            
            IconButton:
                text: '🔄'
                on_release: app.refresh_addons()
        
        ScrollView:
            BoxLayout:
                id: addons_list
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                padding: dp(12)
                spacing: dp(8)

<ModelsScreen>:
    name: 'models'
    
    BoxLayout:
        orientation: 'vertical'
        
        # Header
        BoxLayout:
            size_hint_y: None
            height: dp(56)
            padding: dp(8)
            spacing: dp(8)
            
            canvas.before:
                Color:
                    rgba: utils.get_color_from_hex('#1E1E1E')
                Rectangle:
                    pos: self.pos
                    size: self.size
            
            IconButton:
                text: '←'
                on_release: app.go_to_chat()
            
            Label:
                text: 'AI Models'
                font_size: sp(18)
                bold: True
                halign: 'left'
                text_size: self.size
            
            IconButton:
                text: '🔄'
                on_release: app.refresh_models()
        
        # Tab bar for Available/Installed
        BoxLayout:
            size_hint_y: None
            height: dp(48)
            
            canvas.before:
                Color:
                    rgba: utils.get_color_from_hex('#1E1E1E')
                Rectangle:
                    pos: self.pos
                    size: self.size
            
            ToggleButton:
                id: available_tab
                text: 'Available'
                group: 'models_tabs'
                state: 'down'
                background_color: 0, 0, 0, 0
                background_normal: ''
                on_state: app.switch_models_tab('available') if self.state == 'down' else None
            
            ToggleButton:
                id: installed_tab
                text: 'Installed'
                group: 'models_tabs'
                background_color: 0, 0, 0, 0
                background_normal: ''
                on_state: app.switch_models_tab('installed') if self.state == 'down' else None
            
            ToggleButton:
                id: recommended_tab
                text: 'Recommended'
                group: 'models_tabs'
                background_color: 0, 0, 0, 0
                background_normal: ''
                on_state: app.switch_models_tab('recommended') if self.state == 'down' else None
        
        # Storage info bar
        BoxLayout:
            size_hint_y: None
            height: dp(36)
            padding: dp(12), dp(4)
            
            canvas.before:
                Color:
                    rgba: utils.get_color_from_hex('#2D2D2D')
                Rectangle:
                    pos: self.pos
                    size: self.size
            
            Label:
                id: storage_info
                text: '0 models installed • 0 MB used'
                font_size: sp(11)
                color: 0.6, 0.6, 0.6, 1
                halign: 'left'
                text_size: self.size
        
        ScrollView:
            BoxLayout:
                id: models_list
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                padding: dp(12)
                spacing: dp(8)
        
        # Import model button
        RoundedButton:
            text: '📥 Import Local Model'
            size_hint_y: None
            height: dp(48)
            on_release: app.import_local_model()

<SideDrawer>:
    size_hint_x: None
    width: dp(280)
    
    canvas.before:
        Color:
            rgba: utils.get_color_from_hex('#1E1E1E')
        Rectangle:
            pos: self.pos
            size: self.size
    
    BoxLayout:
        orientation: 'vertical'
        padding: dp(16)
        spacing: dp(8)
        
        # Logo/Title
        BoxLayout:
            size_hint_y: None
            height: dp(80)
            spacing: dp(12)
            
            Label:
                text: '🤖'
                size_hint_x: None
                width: dp(48)
                font_size: sp(32)
            
            BoxLayout:
                orientation: 'vertical'
                
                Label:
                    text: 'AI Chat Room'
                    font_size: sp(18)
                    bold: True
                    halign: 'left'
                    text_size: self.size
                
                Label:
                    text: 'Gemma 3 4B • Pixel TPU'
                    font_size: sp(11)
                    color: 0.6, 0.6, 0.6, 1
                    halign: 'left'
                    text_size: self.size
        
        # Divider
        Widget:
            size_hint_y: None
            height: dp(1)
            canvas:
                Color:
                    rgba: utils.get_color_from_hex('#2D2D2D')
                Rectangle:
                    pos: self.pos
                    size: self.size
        
        # Menu Items
        DrawerItem:
            icon: '💬'
            text: 'Chat'
            on_release: app.nav_to('main_chat')
        
        DrawerItem:
            icon: '👥'
            text: 'Participants'
            on_release: app.nav_to('participants')
        
        DrawerItem:
            icon: '🔒'
            text: 'Private Chats'
            on_release: app.show_private_chats()
        
        DrawerItem:
            icon: '📄'
            text: 'Documents'
            on_release: app.nav_to('documents')
        
        DrawerItem:
            icon: '🔧'
            text: 'Tools'
            on_release: app.nav_to('tools')
        
        DrawerItem:
            icon: '📦'
            text: 'Add-ons'
            on_release: app.nav_to('addons')
        
        DrawerItem:
            icon: '🧠'
            text: 'AI Models'
            on_release: app.nav_to('models')
        
        DrawerItem:
            icon: '⚙️'
            text: 'Settings'
            on_release: app.nav_to('settings')
        
        Widget:  # Spacer
        
        # Version info
        Label:
            text: 'v1.0.0 • Local Mode'
            size_hint_y: None
            height: dp(30)
            font_size: sp(10)
            color: 0.4, 0.4, 0.4, 1

<DrawerItem@BoxLayout>:
    icon: ''
    size_hint_y: None
    height: dp(48)
    spacing: dp(16)
    padding: dp(8)
    
    canvas.before:
        Color:
            rgba: utils.get_color_from_hex('#2D2D2D') if self.state == 'down' else (0, 0, 0, 0)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(8)]
    
    Label:
        text: root.icon
        size_hint_x: None
        width: dp(32)
        font_size: sp(20)
    
    Label:
        text: root.text
        font_size: sp(15)
        halign: 'left'
        text_size: self.size

'''

# ============================================
# Widget Classes
# ============================================

class ChatBubble(BoxLayout):
    """Chat message bubble widget."""
    sender = StringProperty('')
    content = StringProperty('')
    timestamp = StringProperty('')
    avatar = StringProperty('🤖')
    is_user = BooleanProperty(False)
    is_private = BooleanProperty(False)
    bubble_color = ListProperty([0.18, 0.18, 0.24, 1])
    sender_color = ListProperty([1, 1, 1, 1])


class AIParticipantCard(BoxLayout):
    """Card for displaying an AI participant."""
    ai_id = StringProperty('')
    display_name = StringProperty('')
    avatar = StringProperty('🤖')
    personality = StringProperty('')
    ai_color = StringProperty('#FFFFFF')
    emotion_emoji = StringProperty('😊')
    is_active = BooleanProperty(True)
    is_selected = BooleanProperty(False)
    
    def toggle_active(self, active):
        """Toggle the AI's active state."""
        app = App.get_running_app()
        app.set_ai_active(self.ai_id, active)


class PrivateChatItem(BoxLayout):
    """Item for displaying a private conversation."""
    participant_id = StringProperty('')
    participant_name = StringProperty('')
    participant_avatar = StringProperty('🤖')
    last_message = StringProperty('')
    timestamp = StringProperty('')
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            app = App.get_running_app()
            app.open_private_chat(self.participant_id)
            return True
        return super().on_touch_down(touch)


class DocumentCard(BoxLayout):
    """Card for displaying an uploaded document."""
    doc_id = StringProperty('')
    doc_name = StringProperty('')
    doc_info = StringProperty('')
    
    def remove_document(self):
        app = App.get_running_app()
        app.remove_document(self.doc_id)


class ToolCard(BoxLayout):
    """Card for displaying a tool."""
    tool_name = StringProperty('')
    tool_desc = StringProperty('')
    tool_icon = StringProperty('🔧')


class SideDrawer(BoxLayout):
    """Side navigation drawer."""
    pass


class MainChatScreen(Screen):
    """Main chat screen."""
    pass


class ParticipantsScreen(Screen):
    """AI participants management screen."""
    pass


class SettingsScreen(Screen):
    """Settings screen."""
    pass


class DocumentsScreen(Screen):
    """Documents management screen."""
    pass


class ToolsScreen(Screen):
    """Tools screen."""
    pass


class AddonsScreen(Screen):
    """Add-ons screen."""
    pass


class ModelsScreen(Screen):
    """AI Models download and management screen."""
    pass


# ============================================
# Main Application
# ============================================

class AIChatRoomApp(App):
    """Main Kivy application with full GUI."""
    
    # Properties for data binding
    user_name = StringProperty('User')
    current_model = StringProperty('ollama/gemma3:4b')
    is_connected = BooleanProperty(False)
    is_hosting = BooleanProperty(False)
    share_code = StringProperty('')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = 'AI Chat Room'
        
        # State management
        self.state_manager = get_state_manager()
        self.addon_manager = get_addon_manager()
        self.model_manager = get_model_manager()
        
        # AI participants
        self.ai_participants: Dict[str, Dict] = {}
        self.active_ais: List[str] = []
        
        # Chat state
        self.messages: List[Dict] = []
        self.documents: Dict[str, Dict] = {}
        self.active_document: Optional[str] = None
        
        # Private chat state
        self.private_chat_partner: Optional[str] = None
        self.private_conversations: Dict[str, List[Dict]] = {}
        
        # Drawer state
        self.drawer_open = False
        self.drawer_widget = None
        
        # Initialize default AIs
        self._init_default_ais()
    
    def _init_default_ais(self):
        """Initialize default AI participants."""
        for p in DEFAULT_PERSONALITIES:
            self.ai_participants[p['id']] = {
                'id': p['id'],
                'name': p['name'],
                'display_name': p['name'],
                'avatar': p['avatar'],
                'personality': p['personality'],
                'color': p['color'],
                'is_active': p['id'] in ['nova', 'echo', 'sage'],  # Default active
                'emotion': 'neutral',
                'emotion_emoji': '😊',
            }
        
        self.active_ais = ['nova', 'echo', 'sage']
        
        # Load saved state if available
        if self.state_manager:
            for ai_id, ai_data in self.ai_participants.items():
                state = self.state_manager.get_state(ai_id)
                if state:
                    ai_data['display_name'] = state.display_name
                    ai_data['emotion'] = state.current_emotion
                    ai_data['is_active'] = state.is_active
    
    def build(self):
        """Build the application UI."""
        Builder.load_string(KV)
        
        # Set window background color
        Window.clearcolor = get_color_from_hex(COLORS['background'])
        
        # Create root layout with drawer
        self.root_layout = FloatLayout()
        
        # Screen manager
        self.sm = ScreenManager(transition=SlideTransition())
        self.sm.add_widget(MainChatScreen())
        self.sm.add_widget(ParticipantsScreen())
        self.sm.add_widget(SettingsScreen())
        self.sm.add_widget(DocumentsScreen())
        self.sm.add_widget(ToolsScreen())
        self.sm.add_widget(AddonsScreen())
        self.sm.add_widget(ModelsScreen())
        
        self.root_layout.add_widget(self.sm)
        
        # Create drawer (initially hidden)
        self.drawer_widget = SideDrawer()
        self.drawer_widget.x = -dp(280)
        self.root_layout.add_widget(self.drawer_widget)
        
        # Load add-ons
        if self.addon_manager:
            count = self.addon_manager.load_all()
            if count > 0:
                print(f"Loaded {count} add-ons")
        
        return self.root_layout
    
    def on_start(self):
        """Called when the app starts."""
        # Add welcome message
        self.add_system_message("👋 Welcome to AI Chat Room!")
        self.add_system_message("💡 Type a message to chat with AI participants.")
        self.add_system_message("📱 Optimized for Pixel 10 Pro with Gemma 3 4B")
        
        # Update active AIs bar
        self.update_active_ais_bar()
        
        # Load saved settings
        self._load_settings()
    
    def _load_settings(self):
        """Load saved settings."""
        if self.state_manager:
            self.user_name = self.state_manager.get_setting('user_name', 'User')
            self.current_model = self.state_manager.get_setting('model', 'ollama/gemma3:4b')
            
            # Update settings screen
            settings = self.sm.get_screen('settings')
            settings.ids.user_name_input.text = self.user_name
            settings.ids.model_spinner.text = self.current_model
    
    # ========== Navigation ==========
    
    def toggle_drawer(self):
        """Toggle the side drawer."""
        if self.drawer_open:
            anim = Animation(x=-dp(280), duration=0.2)
            anim.start(self.drawer_widget)
            self.drawer_open = False
        else:
            anim = Animation(x=0, duration=0.2)
            anim.start(self.drawer_widget)
            self.drawer_open = True
    
    def nav_to(self, screen_name):
        """Navigate to a screen."""
        self.sm.current = screen_name
        if self.drawer_open:
            self.toggle_drawer()
    
    def go_to_chat(self):
        """Go back to main chat."""
        self.sm.current = 'main_chat'
    
    def show_settings(self):
        """Show settings screen."""
        self.sm.current = 'settings'
    
    def show_participants(self):
        """Show participants screen."""
        self.update_participants_list()
        self.sm.current = 'participants'
    
    def show_private_chats(self):
        """Show private chats tab in participants."""
        self.update_private_chats_list()
        self.sm.current = 'participants'
        if self.drawer_open:
            self.toggle_drawer()
    
    # ========== Chat Functions ==========
    
    def send_message(self):
        """Send a message from the user."""
        chat_screen = self.sm.get_screen('main_chat')
        message_input = chat_screen.ids.message_input
        content = message_input.text.strip()
        
        if not content:
            return
        
        message_input.text = ''
        
        # Check for commands
        if content.startswith('/'):
            self.handle_command(content)
            return
        
        # Check if in private chat
        if self.private_chat_partner:
            self.send_private_message(content)
        else:
            # Add user message to public chat
            self.add_message(self.user_name, content, is_user=True)
            
            # Get AI responses
            Clock.schedule_once(lambda dt: self.get_ai_responses(content), 0.3)
    
    def add_message(self, sender: str, content: str, is_user: bool = False, 
                   is_private: bool = False, avatar: str = None, color: str = None):
        """Add a message to the chat."""
        chat_screen = self.sm.get_screen('main_chat')
        chat_history = chat_screen.ids.chat_history
        
        # Determine avatar and color
        if is_user:
            avatar = '👤'
            bubble_color = get_color_from_hex(COLORS['user_message'])
            sender_color = [0.5, 1, 0.5, 1]
        elif sender == 'System':
            avatar = 'ℹ️'
            bubble_color = get_color_from_hex(COLORS['system_message'])
            sender_color = [0.7, 0.7, 0.7, 1]
        elif is_private:
            # Find AI info
            ai_info = None
            for ai_id, ai in self.ai_participants.items():
                if ai['display_name'] == sender or ai['name'] == sender:
                    ai_info = ai
                    break
            avatar = ai_info['avatar'] if ai_info else '🔒'
            bubble_color = get_color_from_hex(COLORS['private_message'])
            sender_color = list(get_color_from_hex(ai_info['color'])) if ai_info else [1, 0.8, 0.8, 1]
        else:
            # Find AI info
            ai_info = None
            for ai_id, ai in self.ai_participants.items():
                if ai['display_name'] == sender or ai['name'] == sender:
                    ai_info = ai
                    break
            avatar = ai_info['avatar'] if ai_info else '🤖'
            bubble_color = get_color_from_hex(COLORS['ai_message'])
            sender_color = list(get_color_from_hex(ai_info['color'])) if ai_info else [1, 1, 1, 1]
        
        # Create bubble
        bubble = ChatBubble()
        bubble.sender = sender
        bubble.content = content
        bubble.timestamp = datetime.now().strftime('%H:%M')
        bubble.avatar = avatar
        bubble.is_user = is_user
        bubble.is_private = is_private
        bubble.bubble_color = bubble_color
        bubble.sender_color = sender_color
        
        chat_history.add_widget(bubble)
        
        # Scroll to bottom
        chat_scroll = chat_screen.ids.chat_scroll
        Clock.schedule_once(lambda dt: setattr(chat_scroll, 'scroll_y', 0), 0.1)
        
        # Save to state
        self.messages.append({
            'sender': sender,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'is_user': is_user,
            'is_private': is_private
        })
    
    def add_system_message(self, content: str):
        """Add a system message."""
        self.add_message('System', content)
    
    def get_ai_responses(self, user_message: str):
        """Get responses from active AI participants."""
        # random already imported at top
        
        for ai_id in self.active_ais:
            ai = self.ai_participants.get(ai_id)
            if not ai or not ai.get('is_active'):
                continue
            
            # In production, this would call the actual AI model
            # For now, simulate responses
            responses = [
                f"That's fascinating! I'd love to explore that idea further.",
                f"Interesting perspective on that topic.",
                f"I have some thoughts on this that might be helpful.",
                f"Let me think about that for a moment...",
                f"That's a great question to consider.",
            ]
            
            # Customize based on personality
            if 'analytical' in ai['personality'].lower():
                responses.append("From an analytical standpoint, this is quite intriguing.")
            if 'creative' in ai['personality'].lower():
                responses.append("That sparks some creative ideas for me!")
            if 'wise' in ai['personality'].lower():
                responses.append("Ancient wisdom suggests we should consider all perspectives.")
            
            response = random.choice(responses)
            
            # Schedule staggered responses
            delay = 0.5 + (self.active_ais.index(ai_id) * 0.8)
            Clock.schedule_once(
                lambda dt, a=ai, r=response: self.add_message(a['display_name'], r, avatar=a['avatar']),
                delay
            )
    
    def handle_command(self, command: str):
        """Handle a chat command."""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd == '/help':
            self.add_system_message(
                "📖 Commands:\n"
                "/help - Show this help\n"
                "/clear - Clear chat\n"
                "/private <name> - Start private chat\n"
                "/endprivate - End private chat\n"
                "/upload - Upload document\n"
                "/tools - Show tools\n"
                "/addons - Show add-ons\n"
                "/rename <ai> <newname> - Rename AI\n"
                "/add <ai_id> - Add AI to chat\n"
                "/remove <ai_id> - Remove AI from chat"
            )
        elif cmd == '/clear':
            self.clear_chat()
        elif cmd == '/private':
            if args:
                self.start_private_chat(args)
            else:
                self.add_system_message("Usage: /private <ai_name>")
        elif cmd == '/endprivate':
            self.end_private_chat()
        elif cmd == '/upload':
            self.show_file_chooser()
        elif cmd == '/tools':
            self.nav_to('tools')
        elif cmd == '/addons':
            self.nav_to('addons')
        elif cmd == '/rename':
            parts = args.split(maxsplit=1)
            if len(parts) == 2:
                self.rename_ai(parts[0], parts[1])
            else:
                self.add_system_message("Usage: /rename <ai_id> <new_name>")
        elif cmd == '/add':
            if args:
                self.activate_ai(args.lower())
            else:
                self.add_system_message("Usage: /add <ai_id>")
        elif cmd == '/remove':
            if args:
                self.deactivate_ai(args.lower())
            else:
                self.add_system_message("Usage: /remove <ai_id>")
        else:
            self.add_system_message(f"Unknown command: {cmd}")
    
    def clear_chat(self):
        """Clear the chat history."""
        chat_screen = self.sm.get_screen('main_chat')
        chat_history = chat_screen.ids.chat_history
        chat_history.clear_widgets()
        self.messages.clear()
        self.add_system_message("💬 Chat cleared.")
    
    # ========== Private Chat ==========
    
    def start_private_chat(self, partner_name: str):
        """Start a private conversation."""
        # Find the AI by name
        partner_id = None
        for ai_id, ai in self.ai_participants.items():
            if ai['name'].lower() == partner_name.lower() or ai['display_name'].lower() == partner_name.lower():
                partner_id = ai_id
                break
        
        if not partner_id:
            self.add_system_message(f"❌ AI '{partner_name}' not found.")
            return
        
        self.private_chat_partner = partner_id
        ai = self.ai_participants[partner_id]
        
        # Show private chat bar
        chat_screen = self.sm.get_screen('main_chat')
        private_bar = chat_screen.ids.private_chat_bar
        private_label = chat_screen.ids.private_chat_label
        
        private_label.text = f"🔒 Private chat with {ai['avatar']} {ai['display_name']}"
        
        anim = Animation(height=dp(40), opacity=1, duration=0.2)
        anim.start(private_bar)
        
        self.add_system_message(f"🔒 Started private chat with {ai['display_name']}")
    
    def end_private_chat(self):
        """End the current private conversation."""
        if not self.private_chat_partner:
            return
        
        ai = self.ai_participants.get(self.private_chat_partner)
        self.private_chat_partner = None
        
        # Hide private chat bar
        chat_screen = self.sm.get_screen('main_chat')
        private_bar = chat_screen.ids.private_chat_bar
        
        anim = Animation(height=0, opacity=0, duration=0.2)
        anim.start(private_bar)
        
        if ai:
            self.add_system_message(f"🔓 Ended private chat with {ai['display_name']}")
    
    def send_private_message(self, content: str):
        """Send a private message."""
        if not self.private_chat_partner:
            return
        
        ai = self.ai_participants.get(self.private_chat_partner)
        if not ai:
            return
        
        # Add user's private message
        self.add_message(
            f"{self.user_name} → {ai['display_name']}", 
            content, 
            is_user=True, 
            is_private=True
        )
        
        # Save to conversation history
        conv_key = f"{self.user_name}__{ai['id']}"
        if conv_key not in self.private_conversations:
            self.private_conversations[conv_key] = []
        self.private_conversations[conv_key].append({
            'sender': self.user_name,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        
        # Get AI response
        Clock.schedule_once(lambda dt: self.get_private_ai_response(ai, content), 0.5)
    
    def get_private_ai_response(self, ai: Dict, user_message: str):
        """Get a private response from an AI."""
        # random already imported at top
        
        # Simulate private response (in production, use actual AI)
        private_responses = [
            f"*speaking privately* I appreciate you reaching out directly.",
            f"Just between us, I think that's a wonderful idea.",
            f"In this private conversation, I can share more openly...",
            f"Thank you for this one-on-one chat. Here's my thought...",
        ]
        
        response = random.choice(private_responses)
        
        self.add_message(
            f"{ai['display_name']} → {self.user_name}",
            response,
            is_private=True,
            avatar=ai['avatar']
        )
    
    def open_private_chat(self, participant_id: str):
        """Open a private chat from the list."""
        ai = self.ai_participants.get(participant_id)
        if ai:
            self.start_private_chat(ai['name'])
            self.go_to_chat()
    
    # ========== AI Management ==========
    
    def update_active_ais_bar(self):
        """Update the active AIs bar at the top of chat."""
        chat_screen = self.sm.get_screen('main_chat')
        active_bar = chat_screen.ids.active_ais_bar
        active_bar.clear_widgets()
        
        for ai_id in self.active_ais:
            ai = self.ai_participants.get(ai_id)
            if not ai:
                continue
            
            btn = Button(
                text=f"{ai['avatar']} {ai['display_name']}",
                size_hint=(None, None),
                size=(dp(120), dp(44)),
                background_color=get_color_from_hex('#2D2D2D'),
                on_release=lambda x, a=ai: self.show_ai_options(a)
            )
            active_bar.add_widget(btn)
    
    def show_ai_options(self, ai: Dict):
        """Show options for an AI participant."""
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20))
        
        # AI info
        info = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(12))
        info.add_widget(Label(text=ai['avatar'], font_size=sp(40), size_hint_x=None, width=dp(50)))
        
        info_text = BoxLayout(orientation='vertical')
        info_text.add_widget(Label(text=ai['display_name'], font_size=sp(18), bold=True, halign='left', text_size=(dp(200), None)))
        info_text.add_widget(Label(text=ai['personality'], font_size=sp(12), color=(0.7, 0.7, 0.7, 1), halign='left', text_size=(dp(200), None)))
        info.add_widget(info_text)
        content.add_widget(info)
        
        # Buttons
        private_btn = Button(text='🔒 Private Chat', size_hint_y=None, height=dp(48))
        private_btn.bind(on_release=lambda x: [popup.dismiss(), self.start_private_chat(ai['name'])])
        content.add_widget(private_btn)
        
        rename_btn = Button(text='✏️ Rename', size_hint_y=None, height=dp(48))
        rename_btn.bind(on_release=lambda x: [popup.dismiss(), self.show_rename_dialog(ai)])
        content.add_widget(rename_btn)
        
        remove_btn = Button(text='➖ Remove from Chat', size_hint_y=None, height=dp(48))
        remove_btn.bind(on_release=lambda x: [popup.dismiss(), self.deactivate_ai(ai['id'])])
        content.add_widget(remove_btn)
        
        popup = Popup(
            title=f"AI Options",
            content=content,
            size_hint=(0.8, None),
            height=dp(300)
        )
        popup.open()
    
    def show_rename_dialog(self, ai: Dict):
        """Show dialog to rename an AI."""
        content = BoxLayout(orientation='vertical', spacing=dp(15), padding=dp(20))
        
        content.add_widget(Label(
            text=f"Rename {ai['display_name']}",
            font_size=sp(16)
        ))
        
        name_input = TextInput(
            text=ai['display_name'],
            multiline=False,
            size_hint_y=None,
            height=dp(48),
            background_color=get_color_from_hex('#2D2D2D'),
            foreground_color=(1, 1, 1, 1)
        )
        content.add_widget(name_input)
        
        buttons = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        
        cancel_btn = Button(text='Cancel')
        save_btn = Button(text='Save')
        
        buttons.add_widget(cancel_btn)
        buttons.add_widget(save_btn)
        content.add_widget(buttons)
        
        popup = Popup(
            title="Rename AI",
            content=content,
            size_hint=(0.8, None),
            height=dp(220)
        )
        
        cancel_btn.bind(on_release=popup.dismiss)
        save_btn.bind(on_release=lambda x: [self.rename_ai(ai['id'], name_input.text), popup.dismiss()])
        
        popup.open()
    
    def rename_ai(self, ai_id: str, new_name: str):
        """Rename an AI participant."""
        if ai_id not in self.ai_participants:
            self.add_system_message(f"❌ AI '{ai_id}' not found.")
            return
        
        ai = self.ai_participants[ai_id]
        old_name = ai['display_name']
        ai['display_name'] = new_name
        
        # Save to state
        if self.state_manager:
            state = self.state_manager.get_state(ai_id)
            if state:
                state.display_name = new_name
                self.state_manager.save_state(state)
        
        self.add_system_message(f"✏️ {old_name} is now known as {new_name}")
        self.update_active_ais_bar()
        self.update_participants_list()
    
    def activate_ai(self, ai_id: str):
        """Add an AI to the active chat."""
        if ai_id not in self.ai_participants:
            self.add_system_message(f"❌ AI '{ai_id}' not found.")
            return
        
        if ai_id in self.active_ais:
            self.add_system_message(f"AI '{ai_id}' is already active.")
            return
        
        if len(self.active_ais) >= 10:
            self.add_system_message("❌ Maximum 10 AI participants allowed.")
            return
        
        self.active_ais.append(ai_id)
        ai = self.ai_participants[ai_id]
        ai['is_active'] = True
        
        # Save to state
        if self.state_manager:
            state = self.state_manager.get_state(ai_id)
            if state:
                state.is_active = True
                self.state_manager.save_state(state)
        
        self.add_system_message(f"➕ {ai['avatar']} {ai['display_name']} joined the chat!")
        self.update_active_ais_bar()
    
    def deactivate_ai(self, ai_id: str):
        """Remove an AI from the active chat."""
        if ai_id not in self.active_ais:
            return
        
        self.active_ais.remove(ai_id)
        ai = self.ai_participants.get(ai_id)
        if ai:
            ai['is_active'] = False
            
            # Save to state
            if self.state_manager:
                state = self.state_manager.get_state(ai_id)
                if state:
                    state.is_active = False
                    self.state_manager.save_state(state)
            
            self.add_system_message(f"➖ {ai['avatar']} {ai['display_name']} left the chat.")
        
        self.update_active_ais_bar()
    
    def set_ai_active(self, ai_id: str, active: bool):
        """Set whether an AI is active."""
        if active:
            self.activate_ai(ai_id)
        else:
            self.deactivate_ai(ai_id)
    
    def update_participants_list(self):
        """Update the participants screen lists."""
        try:
            participants_screen = self.sm.get_screen('participants')
            
            # Active list
            active_list = participants_screen.ids.active_participants_list
            active_list.clear_widgets()
            
            for ai_id in self.active_ais:
                ai = self.ai_participants.get(ai_id)
                if ai:
                    card = AIParticipantCard()
                    card.ai_id = ai_id
                    card.display_name = ai['display_name']
                    card.avatar = ai['avatar']
                    card.personality = ai['personality']
                    card.ai_color = ai['color']
                    card.emotion_emoji = ai.get('emotion_emoji', '😊')
                    card.is_active = True
                    active_list.add_widget(card)
            
            # All list
            all_list = participants_screen.ids.all_participants_list
            all_list.clear_widgets()
            
            for ai_id, ai in self.ai_participants.items():
                card = AIParticipantCard()
                card.ai_id = ai_id
                card.display_name = ai['display_name']
                card.avatar = ai['avatar']
                card.personality = ai['personality']
                card.ai_color = ai['color']
                card.emotion_emoji = ai.get('emotion_emoji', '😊')
                card.is_active = ai_id in self.active_ais
                all_list.add_widget(card)
        except Exception as e:
            print(f"Error updating participants list: {e}")
    
    def update_private_chats_list(self):
        """Update the private chats list."""
        try:
            participants_screen = self.sm.get_screen('participants')
            private_list = participants_screen.ids.private_chats_list
            private_list.clear_widgets()
            
            # Add all AIs as potential private chat partners
            for ai_id, ai in self.ai_participants.items():
                item = PrivateChatItem()
                item.participant_id = ai_id
                item.participant_name = ai['display_name']
                item.participant_avatar = ai['avatar']
                
                # Get last message if any
                conv_key = f"{self.user_name}__{ai_id}"
                if conv_key in self.private_conversations and self.private_conversations[conv_key]:
                    last_msg = self.private_conversations[conv_key][-1]
                    item.last_message = last_msg['content']
                    item.timestamp = datetime.fromisoformat(last_msg['timestamp']).strftime('%H:%M')
                else:
                    item.last_message = "Start a private conversation"
                    item.timestamp = ""
                
                private_list.add_widget(item)
        except Exception as e:
            print(f"Error updating private chats list: {e}")
    
    def show_add_ai_dialog(self):
        """Show dialog to add an AI."""
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(15))
        
        content.add_widget(Label(
            text="Add AI to Chat",
            font_size=sp(16),
            size_hint_y=None,
            height=dp(30)
        ))
        
        # List inactive AIs
        scroll = ScrollView(size_hint_y=1)
        ai_list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(8))
        ai_list.bind(minimum_height=ai_list.setter('height'))
        
        for ai_id, ai in self.ai_participants.items():
            if ai_id not in self.active_ais:
                btn = Button(
                    text=f"{ai['avatar']} {ai['display_name']}",
                    size_hint_y=None,
                    height=dp(48)
                )
                btn.bind(on_release=lambda x, a_id=ai_id: [self.activate_ai(a_id), popup.dismiss()])
                ai_list.add_widget(btn)
        
        if ai_list.children:
            scroll.add_widget(ai_list)
            content.add_widget(scroll)
        else:
            content.add_widget(Label(text="All AIs are already active!"))
        
        close_btn = Button(text='Close', size_hint_y=None, height=dp(48))
        content.add_widget(close_btn)
        
        popup = Popup(
            title="Add AI",
            content=content,
            size_hint=(0.85, 0.7)
        )
        
        close_btn.bind(on_release=popup.dismiss)
        popup.open()
    
    # ========== Documents ==========
    
    def show_file_chooser(self):
        """Show file chooser for document upload."""
        content = BoxLayout(orientation='vertical', spacing=dp(10))
        
        # Determine start path
        start_path = os.path.expanduser('~')
        if os.path.exists('/storage/emulated/0'):
            start_path = '/storage/emulated/0'
        
        file_chooser = FileChooserListView(
            path=start_path,
            filters=['*.txt', '*.md', '*.json', '*.csv', '*.py', '*.js', '*.html']
        )
        content.add_widget(file_chooser)
        
        buttons = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        
        cancel_btn = Button(text='Cancel')
        select_btn = Button(text='Select')
        
        buttons.add_widget(cancel_btn)
        buttons.add_widget(select_btn)
        content.add_widget(buttons)
        
        popup = Popup(
            title='Select Document',
            content=content,
            size_hint=(0.95, 0.9)
        )
        
        cancel_btn.bind(on_release=popup.dismiss)
        select_btn.bind(on_release=lambda x: self.upload_file(file_chooser.selection, popup))
        
        popup.open()
    
    def upload_file(self, selection, popup):
        """Upload selected file."""
        if not selection:
            return
        
        filepath = selection[0]
        filename = os.path.basename(filepath)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            file_size = os.path.getsize(filepath)
            
            self.documents[filename] = {
                'name': filename,
                'path': filepath,
                'content': content,
                'size': file_size
            }
            self.active_document = filename
            
            # Update document bar
            self.show_document_bar(filename)
            
            self.add_system_message(f"📄 Document uploaded: {filename} ({file_size/1024:.1f} KB)")
            popup.dismiss()
            
        except Exception as e:
            self.add_system_message(f"❌ Error uploading file: {e}")
            popup.dismiss()
    
    def show_document_bar(self, filename: str):
        """Show the document indicator bar."""
        chat_screen = self.sm.get_screen('main_chat')
        doc_bar = chat_screen.ids.document_bar
        doc_label = chat_screen.ids.document_label
        
        doc_label.text = filename
        
        anim = Animation(height=dp(40), opacity=1, duration=0.2)
        anim.start(doc_bar)
    
    def clear_document(self):
        """Clear the active document."""
        if self.active_document:
            del self.documents[self.active_document]
            self.active_document = None
        
        chat_screen = self.sm.get_screen('main_chat')
        doc_bar = chat_screen.ids.document_bar
        
        anim = Animation(height=0, opacity=0, duration=0.2)
        anim.start(doc_bar)
        
        self.add_system_message("📄 Document cleared.")
    
    def remove_document(self, doc_id: str):
        """Remove a document from the list."""
        if doc_id in self.documents:
            del self.documents[doc_id]
            if self.active_document == doc_id:
                self.active_document = None
                self.clear_document()
            self.update_documents_list()
            self.add_system_message(f"📄 Document removed: {doc_id}")
    
    def update_documents_list(self):
        """Update the documents screen list."""
        try:
            docs_screen = self.sm.get_screen('documents')
            docs_list = docs_screen.ids.documents_list
            docs_list.clear_widgets()
            
            if not self.documents:
                docs_list.add_widget(Label(
                    text="No documents uploaded.\n\nTap + to add a document.",
                    halign='center'
                ))
                return
            
            for doc_id, doc in self.documents.items():
                card = DocumentCard()
                card.doc_id = doc_id
                card.doc_name = doc['name']
                card.doc_info = f"{doc['size']/1024:.1f} KB"
                docs_list.add_widget(card)
        except Exception as e:
            print(f"Error updating documents list: {e}")
    
    def show_attachment_menu(self):
        """Show attachment options menu."""
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(15))
        
        doc_btn = Button(text='📄 Document', size_hint_y=None, height=dp(48))
        doc_btn.bind(on_release=lambda x: [popup.dismiss(), self.show_file_chooser()])
        content.add_widget(doc_btn)
        
        camera_btn = Button(text='📷 Camera', size_hint_y=None, height=dp(48))
        camera_btn.bind(on_release=lambda x: [popup.dismiss(), self.add_system_message("📷 Camera coming soon!")])
        content.add_widget(camera_btn)
        
        gallery_btn = Button(text='🖼️ Gallery', size_hint_y=None, height=dp(48))
        gallery_btn.bind(on_release=lambda x: [popup.dismiss(), self.add_system_message("🖼️ Gallery coming soon!")])
        content.add_widget(gallery_btn)
        
        popup = Popup(
            title='Attach',
            content=content,
            size_hint=(0.7, None),
            height=dp(220)
        )
        popup.open()
    
    # ========== Tools ==========
    
    def update_tools_list(self):
        """Update the tools screen list."""
        try:
            tools_screen = self.sm.get_screen('tools')
            tools_list = tools_screen.ids.tools_list
            tools_list.clear_widgets()
            
            # Define available tools
            tools = [
                {'name': 'calculate', 'icon': '🔢', 'desc': 'Perform mathematical calculations'},
                {'name': 'unit_convert', 'icon': '📏', 'desc': 'Convert between units'},
                {'name': 'get_current_time', 'icon': '🕐', 'desc': 'Get current date and time'},
                {'name': 'calculate_date', 'icon': '📅', 'desc': 'Calculate date differences'},
                {'name': 'word_count', 'icon': '📝', 'desc': 'Count words in text'},
                {'name': 'search_text', 'icon': '🔍', 'desc': 'Search for patterns in text'},
                {'name': 'extract_urls', 'icon': '🔗', 'desc': 'Extract URLs from text'},
                {'name': 'extract_emails', 'icon': '📧', 'desc': 'Extract email addresses'},
                {'name': 'json_parse', 'icon': '📋', 'desc': 'Parse and format JSON'},
                {'name': 'list_files', 'icon': '📁', 'desc': 'List files in a directory'},
                {'name': 'read_file', 'icon': '📖', 'desc': 'Read file contents'},
                {'name': 'get_system_info', 'icon': '💻', 'desc': 'Get system information'},
            ]
            
            for tool in tools:
                card = ToolCard()
                card.tool_name = tool['name']
                card.tool_icon = tool['icon']
                card.tool_desc = tool['desc']
                tools_list.add_widget(card)
        except Exception as e:
            print(f"Error updating tools list: {e}")
    
    # ========== Add-ons ==========
    
    def refresh_addons(self):
        """Refresh the add-ons list."""
        try:
            addons_screen = self.sm.get_screen('addons')
            addons_list = addons_screen.ids.addons_list
            addons_list.clear_widgets()
            
            if not self.addon_manager:
                addons_list.add_widget(Label(text='Add-on system not available'))
                return
            
            addons = self.addon_manager.list_addons()
            
            if not addons:
                addons_list.add_widget(Label(
                    text='No add-ons installed.\n\nAdd add-ons to the addons directory.',
                    halign='center'
                ))
                return
            
            for addon in addons:
                item = BoxLayout(size_hint_y=None, height=dp(70), padding=dp(10))
                item.canvas.before.add(Color(*get_color_from_hex('#2D2D2D')))
                
                info = BoxLayout(orientation='vertical')
                info.add_widget(Label(text=addon['name'], bold=True, halign='left', text_size=(dp(200), None)))
                info.add_widget(Label(text=addon.get('description', '')[:50], font_size=sp(11), color=(0.6, 0.6, 0.6, 1), halign='left', text_size=(dp(200), None)))
                item.add_widget(info)
                
                switch = Switch(active=addon.get('enabled', True), size_hint_x=None, width=dp(60))
                item.add_widget(switch)
                
                addons_list.add_widget(item)
        except Exception as e:
            print(f"Error refreshing addons: {e}")
    
    # ========== Settings ==========
    
    def save_settings(self):
        """Save current settings."""
        settings = self.sm.get_screen('settings')
        
        self.user_name = settings.ids.user_name_input.text
        self.current_model = settings.ids.model_spinner.text
        
        # Save to state manager
        if self.state_manager:
            self.state_manager.set_setting('user_name', self.user_name)
            self.state_manager.set_setting('model', self.current_model)
            self.state_manager.set_setting('ollama_url', settings.ids.ollama_url_input.text)
            self.state_manager.save_settings()
        
        self.add_system_message("✅ Settings saved!")
        self.go_to_chat()
    
    def host_room(self):
        """Start hosting a P2P room."""
        self.is_hosting = True
        # Generate a random share code
        import string
        self.share_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        self.add_system_message(f"🌐 Room hosted! Share code: {self.share_code}")
    
    def join_room(self):
        """Join a P2P room."""
        settings = self.sm.get_screen('settings')
        code = settings.ids.join_code_input.text.strip()
        
        if not code:
            self.add_system_message("❌ Please enter a share code.")
            return
        
        self.is_connected = True
        self.add_system_message(f"🌐 Connected to room: {code}")
        self.go_to_chat()
    
    def export_data(self):
        """Export all data."""
        if self.state_manager:
            data = self.state_manager.export_all()
            self.add_system_message("📤 Data exported to Documents/AIChat/backup.json")
        else:
            self.add_system_message("❌ State manager not available")
    
    def import_data(self):
        """Import data from backup."""
        self.show_file_chooser()
    
    # ========== Voice Input ==========
    
    def start_voice_input(self):
        """Start voice input (placeholder)."""
        self.add_system_message("🎤 Voice input coming soon!")
    
    # ========== Model Management ==========
    
    def refresh_models(self):
        """Refresh the models list."""
        self._update_models_screen()
    
    def switch_models_tab(self, tab: str):
        """Switch between Available/Installed/Recommended tabs."""
        self._update_models_screen(tab)
    
    def _update_models_screen(self, tab: str = 'available'):
        """Update the models screen content."""
        try:
            models_screen = self.sm.get_screen('models')
            models_list = models_screen.ids.models_list
            storage_info = models_screen.ids.storage_info
            
            # Clear current list
            models_list.clear_widgets()
            
            if not self.model_manager:
                models_list.add_widget(Label(
                    text="Model manager not available",
                    color=(0.6, 0.6, 0.6, 1)
                ))
                return
            
            # Update storage info
            usage = self.model_manager.get_storage_usage()
            storage_info.text = f"{usage['model_count']} models installed • {usage['total_human']} used"
            
            # Get models based on tab
            if tab == 'installed':
                models = self.model_manager.get_installed_models()
                if not models:
                    models_list.add_widget(Label(
                        text="No models installed yet",
                        size_hint_y=None, height=dp(48),
                        color=(0.6, 0.6, 0.6, 1)
                    ))
                    return
                for model in models:
                    self._add_installed_model_item(models_list, model)
            elif tab == 'recommended':
                # Assume 8GB RAM and TPU for Pixel 10 Pro
                models = self.model_manager.get_recommended_models(device_ram_mb=8192, has_tpu=True)
                for model in models[:5]:  # Top 5 recommendations
                    installed = self.model_manager.is_model_installed(model.id)
                    self._add_model_item(models_list, model, installed, recommended=True)
            else:  # available
                models = self.model_manager.get_available_models()
                for model in models:
                    installed = self.model_manager.is_model_installed(model.id)
                    self._add_model_item(models_list, model, installed)
        except Exception as e:
            print(f"Error updating models screen: {e}")
    
    def _add_model_item(self, container, model, installed: bool, recommended: bool = False):
        """Add a model item to the list."""
        item = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(100), padding=dp(8), spacing=dp(12))
        
        # Background - use callback to redraw on resize/reposition
        def update_canvas(widget, *args):
            self._draw_model_bg(widget, recommended)
        
        with item.canvas.before:
            Color(*get_color_from_hex('#2D2D3D' if recommended else '#2D2D2D'))
            RoundedRectangle(pos=item.pos, size=item.size, radius=[dp(8)])
        item.bind(pos=update_canvas)
        item.bind(size=update_canvas)
        
        # Info section
        info = BoxLayout(orientation='vertical', spacing=dp(4))
        
        # Name row
        name_row = BoxLayout(size_hint_y=None, height=dp(24), spacing=dp(8))
        name_label = Label(text=model.name, bold=True, font_size=sp(14), halign='left', text_size=(dp(200), None))
        name_row.add_widget(name_label)
        
        if installed:
            installed_badge = Label(text='✓', size_hint_x=None, width=dp(24), color=(0.2, 0.8, 0.2, 1))
            name_row.add_widget(installed_badge)
        
        if model.supports_tpu:
            tpu_badge = Label(text='TPU', size_hint_x=None, width=dp(40), font_size=sp(10), color=(0.4, 0.6, 1, 1))
            name_row.add_widget(tpu_badge)
        
        if recommended:
            rec_badge = Label(text='⭐', size_hint_x=None, width=dp(24))
            name_row.add_widget(rec_badge)
        
        info.add_widget(name_row)
        
        # Description
        desc_label = Label(
            text=model.description[:80] + '...' if len(model.description) > 80 else model.description,
            font_size=sp(11), color=(0.7, 0.7, 0.7, 1), halign='left', text_size=(dp(250), None)
        )
        info.add_widget(desc_label)
        
        # Size and RAM info
        size_row = BoxLayout(size_hint_y=None, height=dp(20))
        size_label = Label(
            text=f"📦 {model.size_human} • 💾 {model.required_ram_mb}MB RAM • {model.quantization or 'default'}",
            font_size=sp(10), color=(0.5, 0.5, 0.5, 1), halign='left', text_size=(dp(250), None)
        )
        size_row.add_widget(size_label)
        info.add_widget(size_row)
        
        item.add_widget(info)
        
        # Action button
        if installed:
            btn = Button(text='🗑️', size_hint=(None, None), size=(dp(48), dp(48)), background_color=(0.8, 0.2, 0.2, 1))
            btn.bind(on_release=lambda x, m=model.id: self._delete_model(m))
        else:
            btn = Button(text='⬇️', size_hint=(None, None), size=(dp(48), dp(48)), background_color=(0.2, 0.6, 0.2, 1))
            btn.bind(on_release=lambda x, m=model.id: self._download_model(m))
        
        item.add_widget(btn)
        container.add_widget(item)
    
    def _add_installed_model_item(self, container, model_info: Dict):
        """Add an installed model item to the list."""
        item = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(80), padding=dp(8), spacing=dp(12))
        
        with item.canvas.before:
            Color(*get_color_from_hex('#2D3D2D'))  # Green tint for installed
            RoundedRectangle(pos=item.pos, size=item.size, radius=[dp(8)])
        
        # Info section
        info = BoxLayout(orientation='vertical', spacing=dp(4))
        
        name_label = Label(text=model_info['name'], bold=True, font_size=sp(14), halign='left', text_size=(dp(200), None))
        info.add_widget(name_label)
        
        size_bytes = model_info.get('size_bytes', 0)
        size_str = f"{size_bytes / (1024*1024*1024):.2f} GB" if size_bytes > 1024*1024*1024 else f"{size_bytes / (1024*1024):.1f} MB"
        size_label = Label(text=f"📦 {size_str}", font_size=sp(11), color=(0.6, 0.6, 0.6, 1), halign='left', text_size=(dp(200), None))
        info.add_widget(size_label)
        
        installed_label = Label(text=f"Installed: {model_info.get('installed_at', 'Unknown')}", font_size=sp(10), color=(0.5, 0.5, 0.5, 1), halign='left', text_size=(dp(200), None))
        info.add_widget(installed_label)
        
        item.add_widget(info)
        
        # Actions
        actions = BoxLayout(orientation='vertical', size_hint_x=None, width=dp(60), spacing=dp(4))
        
        use_btn = Button(text='✓', size_hint_y=None, height=dp(36), background_color=(0.2, 0.6, 0.2, 1))
        use_btn.bind(on_release=lambda x, m=model_info['id']: self._use_model(m))
        actions.add_widget(use_btn)
        
        del_btn = Button(text='🗑️', size_hint_y=None, height=dp(36), background_color=(0.6, 0.2, 0.2, 1))
        del_btn.bind(on_release=lambda x, m=model_info['id']: self._delete_model(m))
        actions.add_widget(del_btn)
        
        item.add_widget(actions)
        container.add_widget(item)
    
    def _draw_model_bg(self, widget, recommended: bool = False):
        """Redraw model item background."""
        with widget.canvas.before:
            Color(*get_color_from_hex('#2D2D3D' if recommended else '#2D2D2D'))
            RoundedRectangle(pos=widget.pos, size=widget.size, radius=[dp(8)])
    
    def _download_model(self, model_id: str):
        """Download a model."""
        if not self.model_manager:
            self.add_system_message("❌ Model manager not available")
            return
        
        self.add_system_message(f"⬇️ Starting download of {model_id}...")
        self.add_system_message("📱 This may take a while depending on your connection.")
        
        def progress_callback(progress):
            # Update UI on main thread
            Clock.schedule_once(lambda dt: self._update_download_progress(progress), 0)
        
        def do_download():
            try:
                result = self.model_manager.download_model(model_id, callback=progress_callback)
                if result and result.status == "complete":
                    Clock.schedule_once(lambda dt: self._download_complete(model_id), 0)
                else:
                    error = result.error_message if result else "Unknown error"
                    Clock.schedule_once(lambda dt: self._download_failed(model_id, error), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: self._download_failed(model_id, str(e)), 0)
        
        # Run download in background thread
        import threading
        threading.Thread(target=do_download, daemon=True).start()
    
    def _update_download_progress(self, progress):
        """Update download progress in UI."""
        # Track last reported percentage to report every 10%
        current_ten = int(progress.percent / 10)
        last_ten = getattr(self, '_last_progress_ten', -1)
        
        if current_ten > last_ten:
            self._last_progress_ten = current_ten
            self.add_system_message(f"⬇️ {progress.model_id}: {progress.percent:.0f}% ({progress.speed_human})")
    
    def _download_complete(self, model_id: str):
        """Handle download completion."""
        self._last_progress_ten = -1  # Reset progress tracker
        self.add_system_message(f"✅ {model_id} downloaded successfully!")
        self.refresh_models()
    
    def _download_failed(self, model_id: str, error: str):
        """Handle download failure."""
        self._last_progress_ten = -1  # Reset progress tracker
        self.add_system_message(f"❌ Failed to download {model_id}: {error}")
    
    def _delete_model(self, model_id: str):
        """Delete an installed model."""
        if not self.model_manager:
            return
        
        if self.model_manager.delete_model(model_id):
            self.add_system_message(f"🗑️ Deleted {model_id}")
            self.refresh_models()
        else:
            self.add_system_message(f"❌ Failed to delete {model_id}")
    
    def _use_model(self, model_id: str):
        """Set a model as the current model."""
        if not self.model_manager:
            return
        
        model_path = self.model_manager.get_model_path(model_id)
        if model_path:
            self.current_model = f"ollama/{model_id}"
            self.add_system_message(f"🧠 Now using model: {model_id}")
            
            # Update settings screen
            try:
                settings = self.sm.get_screen('settings')
                settings.ids.model_spinner.text = self.current_model
            except Exception:
                pass
    
    def import_local_model(self):
        """Import a model from local storage."""
        self.show_file_chooser()
        self.add_system_message("📥 Select a model file (.gguf, .onnx, .tflite)")
        # Note: The actual import would be handled in the file chooser callback


# ============================================
# Entry Point
# ============================================

def main():
    """Main entry point for Android app."""
    AIChatRoomApp().run()


if __name__ == '__main__':
    main()
