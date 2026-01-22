#!/usr/bin/env python3
"""
AI Chat Room - Android Application

A Kivy-based Android application for the AI Chat Room.
Provides a native Android experience with support for:
- Multi-AI conversations
- Document upload and analysis
- Tool use
- Add-on/plugin system
- Local Gemma 3 4B model (Pixel TPU optimized)

This file is the main entry point for the Android app.
"""

import os
import sys

# Ensure the app directory is in the path
app_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, app_dir)
sys.path.insert(0, os.path.join(app_dir, 'src'))

# Kivy configuration (must be before importing kivy)
os.environ['KIVY_LOG_LEVEL'] = 'info'

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.recycleview import RecycleView
from kivy.uix.spinner import Spinner
from kivy.properties import StringProperty, ListProperty, BooleanProperty
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder

# Import app modules
try:
    from addons import addon_manager, get_addon_manager
except ImportError:
    addon_manager = None

# Kivy UI definition
KV = '''
#:import utils kivy.utils

<ChatMessage>:
    size_hint_y: None
    height: self.minimum_height
    padding: 10
    
    BoxLayout:
        orientation: 'vertical'
        size_hint_y: None
        height: self.minimum_height
        
        Label:
            text: root.sender
            size_hint_y: None
            height: 20
            font_size: '12sp'
            color: utils.get_color_from_hex('#888888')
            halign: 'left'
            text_size: self.size
        
        Label:
            text: root.content
            size_hint_y: None
            height: self.texture_size[1]
            text_size: self.width, None
            halign: 'left'
            markup: True

<ChatScreen>:
    name: 'chat'
    
    BoxLayout:
        orientation: 'vertical'
        padding: 10
        spacing: 5
        
        # Header
        BoxLayout:
            size_hint_y: None
            height: 50
            spacing: 10
            
            Label:
                text: 'AI Chat Room'
                font_size: '20sp'
                bold: True
                halign: 'left'
                text_size: self.size
            
            Button:
                text: '⚙️'
                size_hint_x: None
                width: 50
                on_release: app.show_settings()
            
            Button:
                text: '📦'
                size_hint_x: None
                width: 50
                on_release: app.show_addons()
        
        # Chat history
        ScrollView:
            id: chat_scroll
            do_scroll_x: False
            
            BoxLayout:
                id: chat_history
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: 5
        
        # Input area
        BoxLayout:
            size_hint_y: None
            height: 60
            spacing: 5
            
            TextInput:
                id: message_input
                hint_text: 'Type a message...'
                multiline: False
                on_text_validate: app.send_message()
            
            Button:
                text: '📎'
                size_hint_x: None
                width: 50
                on_release: app.show_file_chooser()
            
            Button:
                text: 'Send'
                size_hint_x: None
                width: 80
                on_release: app.send_message()

<SettingsScreen>:
    name: 'settings'
    
    BoxLayout:
        orientation: 'vertical'
        padding: 20
        spacing: 10
        
        Label:
            text: 'Settings'
            font_size: '24sp'
            size_hint_y: None
            height: 50
        
        BoxLayout:
            size_hint_y: None
            height: 40
            
            Label:
                text: 'Model:'
                size_hint_x: 0.3
            
            Spinner:
                id: model_spinner
                text: 'ollama/gemma3:4b'
                values: ['ollama/gemma3:4b', 'ollama/gemma3:2b', 'gemini/gemini-2.0-flash']
                size_hint_x: 0.7
        
        BoxLayout:
            size_hint_y: None
            height: 40
            
            Label:
                text: 'API Key:'
                size_hint_x: 0.3
            
            TextInput:
                id: api_key_input
                hint_text: 'Optional for local models'
                password: True
                size_hint_x: 0.7
        
        BoxLayout:
            size_hint_y: None
            height: 40
            
            Label:
                text: 'Ollama URL:'
                size_hint_x: 0.3
            
            TextInput:
                id: ollama_url_input
                text: 'http://localhost:11434'
                size_hint_x: 0.7
        
        Widget:  # Spacer
        
        Button:
            text: 'Back to Chat'
            size_hint_y: None
            height: 50
            on_release: app.go_to_chat()

<AddonsScreen>:
    name: 'addons'
    
    BoxLayout:
        orientation: 'vertical'
        padding: 20
        spacing: 10
        
        Label:
            text: 'Add-ons'
            font_size: '24sp'
            size_hint_y: None
            height: 50
        
        ScrollView:
            BoxLayout:
                id: addons_list
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: 10
        
        BoxLayout:
            size_hint_y: None
            height: 50
            spacing: 10
            
            Button:
                text: 'Refresh'
                on_release: app.refresh_addons()
            
            Button:
                text: 'Back to Chat'
                on_release: app.go_to_chat()

<AddonItem>:
    size_hint_y: None
    height: 80
    padding: 10
    
    canvas.before:
        Color:
            rgba: 0.2, 0.2, 0.2, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [10]
    
    BoxLayout:
        orientation: 'vertical'
        
        Label:
            text: root.addon_name
            font_size: '16sp'
            bold: True
            halign: 'left'
            text_size: self.size
        
        Label:
            text: root.addon_desc
            font_size: '12sp'
            color: 0.7, 0.7, 0.7, 1
            halign: 'left'
            text_size: self.size
    
    Switch:
        id: addon_switch
        active: root.addon_enabled
        size_hint_x: None
        width: 60
        on_active: root.toggle_addon(self.active)
'''


class ChatMessage(BoxLayout):
    """Widget for displaying a chat message."""
    sender = StringProperty('')
    content = StringProperty('')


class AddonItem(BoxLayout):
    """Widget for displaying an add-on in the list."""
    addon_id = StringProperty('')
    addon_name = StringProperty('')
    addon_desc = StringProperty('')
    addon_enabled = BooleanProperty(True)
    
    def toggle_addon(self, active):
        """Toggle the add-on enabled state."""
        app = App.get_running_app()
        if active:
            app.addon_manager.enable_addon(self.addon_id)
        else:
            app.addon_manager.disable_addon(self.addon_id)


class ChatScreen(Screen):
    """Main chat screen."""
    pass


class SettingsScreen(Screen):
    """Settings screen."""
    pass


class AddonsScreen(Screen):
    """Add-ons management screen."""
    pass


class AIChatRoomApp(App):
    """Main Kivy application."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.addon_manager = get_addon_manager() if addon_manager else None
        self.messages = []
        self.ai_participants = [
            {"name": "Nova", "personality": "Curious and analytical"},
            {"name": "Echo", "personality": "Creative and playful"},
            {"name": "Sage", "personality": "Wise and contemplative"},
        ]
    
    def build(self):
        """Build the application UI."""
        Builder.load_string(KV)
        
        self.sm = ScreenManager()
        self.sm.add_widget(ChatScreen())
        self.sm.add_widget(SettingsScreen())
        self.sm.add_widget(AddonsScreen())
        
        # Load add-ons
        if self.addon_manager:
            count = self.addon_manager.load_all()
            print(f"Loaded {count} add-ons")
        
        return self.sm
    
    def on_start(self):
        """Called when the app starts."""
        self.add_system_message("Welcome to AI Chat Room!")
        self.add_system_message("Type a message to chat with AI participants.")
        self.add_system_message("Use /help for available commands.")
    
    def send_message(self):
        """Send a message from the user."""
        chat_screen = self.sm.get_screen('chat')
        message_input = chat_screen.ids.message_input
        content = message_input.text.strip()
        
        if not content:
            return
        
        message_input.text = ''
        
        # Check for commands
        if content.startswith('/'):
            self.handle_command(content)
            return
        
        # Add user message
        self.add_message("You", content)
        
        # Simulate AI responses (in production, this would call the actual AI)
        Clock.schedule_once(lambda dt: self.simulate_ai_response(content), 0.5)
    
    def handle_command(self, command: str):
        """Handle a chat command."""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd == '/help':
            self.add_system_message(
                "Commands:\n"
                "/help - Show this help\n"
                "/tools - List available tools\n"
                "/addons - Manage add-ons\n"
                "/clear - Clear chat history\n"
                "/settings - Open settings"
            )
        elif cmd == '/tools':
            self.add_system_message("Available tools: calculate, unit_convert, "
                                   "get_current_time, word_count, and more.")
        elif cmd == '/addons':
            self.show_addons()
        elif cmd == '/clear':
            self.clear_chat()
        elif cmd == '/settings':
            self.show_settings()
        else:
            # Check add-on commands
            if self.addon_manager:
                addon_commands = self.addon_manager.get_all_commands()
                if cmd in addon_commands:
                    result = addon_commands[cmd](args)
                    self.add_system_message(result)
                    return
            
            self.add_system_message(f"Unknown command: {cmd}")
    
    def simulate_ai_response(self, user_message: str):
        """Simulate AI responses (placeholder for actual AI integration)."""
        import random
        
        responses = [
            f"That's an interesting point about '{user_message[:20]}...'",
            "I'd love to explore that idea further!",
            "From my perspective, this raises some fascinating questions.",
        ]
        
        for ai in self.ai_participants[:1]:  # Just one AI for demo
            response = random.choice(responses)
            self.add_message(ai["name"], response)
    
    def add_message(self, sender: str, content: str):
        """Add a message to the chat history."""
        chat_screen = self.sm.get_screen('chat')
        chat_history = chat_screen.ids.chat_history
        
        msg = ChatMessage()
        msg.sender = sender
        msg.content = content
        chat_history.add_widget(msg)
        
        # Scroll to bottom
        chat_scroll = chat_screen.ids.chat_scroll
        Clock.schedule_once(lambda dt: setattr(chat_scroll, 'scroll_y', 0), 0.1)
    
    def add_system_message(self, content: str):
        """Add a system message."""
        self.add_message("System", f"[color=#888888]{content}[/color]")
    
    def clear_chat(self):
        """Clear the chat history."""
        chat_screen = self.sm.get_screen('chat')
        chat_history = chat_screen.ids.chat_history
        chat_history.clear_widgets()
        self.add_system_message("Chat cleared.")
    
    def show_file_chooser(self):
        """Show file chooser for document upload."""
        content = BoxLayout(orientation='vertical')
        
        file_chooser = FileChooserListView(
            path=os.path.expanduser('~'),
            filters=['*.txt', '*.md', '*.json', '*.csv', '*.py']
        )
        content.add_widget(file_chooser)
        
        buttons = BoxLayout(size_hint_y=None, height=50, spacing=10)
        
        cancel_btn = Button(text='Cancel')
        select_btn = Button(text='Select')
        
        buttons.add_widget(cancel_btn)
        buttons.add_widget(select_btn)
        content.add_widget(buttons)
        
        popup = Popup(
            title='Select Document',
            content=content,
            size_hint=(0.9, 0.9)
        )
        
        cancel_btn.bind(on_release=popup.dismiss)
        select_btn.bind(on_release=lambda x: self.upload_file(
            file_chooser.selection, popup
        ))
        
        popup.open()
    
    def upload_file(self, selection, popup):
        """Upload selected file."""
        if selection:
            filepath = selection[0]
            filename = os.path.basename(filepath)
            self.add_system_message(f"Document uploaded: {filename}")
            popup.dismiss()
    
    def show_settings(self):
        """Show settings screen."""
        self.sm.current = 'settings'
    
    def show_addons(self):
        """Show add-ons screen."""
        self.refresh_addons()
        self.sm.current = 'addons'
    
    def refresh_addons(self):
        """Refresh the add-ons list."""
        addons_screen = self.sm.get_screen('addons')
        addons_list = addons_screen.ids.addons_list
        addons_list.clear_widgets()
        
        if not self.addon_manager:
            label = Label(text='Add-on system not available')
            addons_list.add_widget(label)
            return
        
        for addon_info in self.addon_manager.list_addons():
            item = AddonItem()
            item.addon_id = addon_info['id']
            item.addon_name = addon_info['name']
            item.addon_desc = addon_info['description']
            item.addon_enabled = addon_info.get('enabled', True)
            addons_list.add_widget(item)
        
        if not self.addon_manager.list_addons():
            label = Label(
                text='No add-ons installed.\n\nAdd add-ons to the addons directory.',
                halign='center'
            )
            addons_list.add_widget(label)
    
    def go_to_chat(self):
        """Go back to chat screen."""
        self.sm.current = 'chat'


def main():
    """Main entry point for Android app."""
    AIChatRoomApp().run()


if __name__ == '__main__':
    main()
