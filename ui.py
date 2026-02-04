import os
import time
import random
import math
import tkinter as tk
import customtkinter as ctk
from collections import deque
from PIL import Image, ImageTk, ImageDraw, ImageFilter

# Set CustomTkinter appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class JarvisUI:
    def __init__(self, face_path, size=(760, 760)):
        self.root = ctk.CTk()
        self.root.title("K I R A  •  AI Assistant")
        
        # Get screen size for adaptive window
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate window size (85% of screen for better fit)
        window_width = min(int(screen_width * 0.85), 1100)
        window_height = min(int(screen_height * 0.9), 1000)
        
        # Center window
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(900, 800)
        self.root.resizable(True, True)
        
        # Professional color palette - "Neural Blue" theme
        self.colors = {
            'bg_primary': '#000000',      # Pure black background
            'bg_secondary': '#0A0A0A',    # Slightly lighter black
            'bg_card': '#141414',         # Card/container background
            'accent': '#00D4FF',          # Bright cyan-blue accent
            'accent_hover': '#00B8E6',    # Darker on hover
            'accent_dim': '#0088B3',      # Muted accent
            'success': '#00FF9F',         # Neon green
            'warning': '#FFB800',         # Amber
            'error': '#FF3366',           # Coral red
            'text_primary': '#FFFFFF',    # White text
            'text_secondary': '#A0AEC0',  # Muted gray text
            'glow': '#00D4FF',            # Glow effect color
        }
        
        self.root.configure(fg_color=self.colors['bg_primary'])
        
        # Professional font configuration
        self.fonts = {
            'title': ("SF Pro Display", 24, "bold"),      # Title font
            'subtitle': ("SF Pro Display", 16, "bold"),   # Subtitle
            'body': ("SF Pro Text", 12),                  # Body text
            'body_medium': ("SF Pro Text", 11),           # Smaller body
            'mono': ("JetBrains Mono", 11),              # Monospace
            'button': ("SF Pro Display", 13, "bold"),     # Buttons
            'chat': ("SF Pro Text", 11),                  # Chat messages
        }

        self.size = size
        self.center_y = 0.38

        # Main canvas for face animation with subtle glow border
        self.canvas_container = ctk.CTkFrame(
            self.root,
            fg_color="transparent",
            corner_radius=0
        )
        self.canvas_container.place(relx=0.5, rely=self.center_y, anchor="center")
        
        self.canvas = tk.Canvas(
            self.canvas_container,
            width=size[0],
            height=size[1],
            bg=self.colors['bg_primary'],
            highlightthickness=0
        )
        self.canvas.pack()

        # Control bar - thinking indicator + stop button (higher up)
        self.control_bar = ctk.CTkFrame(
            self.root,
            fg_color="transparent",
            corner_radius=0
        )
        self.control_bar.place(relx=0.5, rely=0.68, anchor="center")

        # Thinking indicator with animated particles
        self.thinking_container = ctk.CTkFrame(
            self.control_bar,
            fg_color="transparent"
        )
        self.thinking_container.pack(side="left", padx=15)
        
        self.thinking_canvas = tk.Canvas(
            self.thinking_container,
            width=250,  # Wider for better text visibility
            height=70,  # Taller
            bg=self.colors['bg_primary'],
            highlightthickness=0
        )
        self.thinking_canvas.pack()
        self.thinking_canvas.pack_forget()  # Hide initially
        
        self.thinking_active = False
        self.thinking_frame_count = 0
        
        # Premium STOP button with hover effects
        self.stop_button_container = ctk.CTkFrame(
            self.control_bar,
            fg_color="transparent"
        )
        self.stop_button_container.pack(side="left", padx=15)
        
        self.stop_button = ctk.CTkButton(
            self.stop_button_container,
            text="⏹  STOP",
            font=self.fonts['button'],
            fg_color=self.colors['error'],
            hover_color="#E62E5C",
            text_color=self.colors['text_primary'],
            corner_radius=25,
            width=160,
            height=50,
            border_width=0,
            cursor="hand2",
            command=self._on_stop_button_click
        )
        self.stop_button.pack(padx=3, pady=3)
        
        # Add subtle hover effect
        self.stop_button.bind('<Enter>', self._on_button_hover)
        self.stop_button.bind('<Leave>', self._on_button_leave)

        # Load face image
        self.face_base = (
            Image.open(face_path)
            .convert("RGBA")
            .resize(size, Image.LANCZOS)
        )

        # Enhanced multi-layer halo
        self.halo_base = self._create_enhanced_halo(size, radius=220, y_offset=-50)
        self.thinking_halo_base = self._create_thinking_halo(size, radius=220, y_offset=-50)

        # Animation state
        self.speaking = False
        self.thinking = False
        self.scale = 1.0
        self.target_scale = 1.0
        self.halo_alpha = 70
        self.target_halo_alpha = 70
        self.last_target_time = time.time()

        # Modern chat container - WIDE and LOW (positioned higher)
        self.chat_outer_container = ctk.CTkFrame(
            self.root,
            fg_color="transparent",
            corner_radius=22
        )
        self.chat_outer_container.place(relx=0.5, rely=0.85, anchor="center")
        
        # Calculate chat width based on window width (90% of window)
        chat_width = int(window_width * 0.90)
        
        self.chat_container = ctk.CTkFrame(
            self.chat_outer_container,
            fg_color=self.colors['bg_secondary'],
            corner_radius=20,
            border_width=2,
            border_color=self.colors['accent'],
            width=chat_width,
            height=240
        )
        self.chat_container.pack(padx=2, pady=2)
        self.chat_container.pack_propagate(False)  # Force size
        
        # Chat header with modern design (minimal height)
        self.chat_header = ctk.CTkFrame(
            self.chat_container,
            fg_color=self.colors['bg_card'],
            corner_radius=18,
            height=35
        )
        self.chat_header.pack(fill="x", padx=4, pady=(4, 0))
        
        self.chat_title = ctk.CTkLabel(
            self.chat_header,
            text="💬  Conversation",
            font=("SF Pro Display", 11, "bold"),
            text_color=self.colors['accent']
        )
        self.chat_title.pack(pady=4)
        
        # Scrollable frame for messages with custom scrollbar
        self.chat_scroll = ctk.CTkScrollableFrame(
            self.chat_container,
            fg_color=self.colors['bg_primary'],
            corner_radius=15,
            scrollbar_button_color=self.colors['accent'],
            scrollbar_button_hover_color=self.colors['accent_hover']
        )
        self.chat_scroll.pack(fill="both", expand=True, padx=4, pady=4)

        self.typing_queue = deque()
        self.is_typing = False
        self.message_count = 0

        # Start animation loop
        self._animate()
        self.root.protocol("WM_DELETE_WINDOW", lambda: os._exit(0))
    
    def _on_button_hover(self, event):
        """Subtle scale effect on button hover."""
        self.stop_button.configure(width=165, height=52)
    
    def _on_button_leave(self, event):
        """Reset button size on hover leave."""
        self.stop_button.configure(width=160, height=50)
    
    def _on_stop_button_click(self):
        """Handle stop button click - interrupts AI response."""
        # Add click feedback
        original_color = self.stop_button.cget('fg_color')
        self.stop_button.configure(fg_color=self.colors['bg_primary'])
        self.root.after(80, lambda: self.stop_button.configure(fg_color=original_color))
        
        # Import and call stop functions
        try:
            from tts import stop_speaking
            stop_speaking()
        except:
            pass
        
        try:
            from speech_to_text import stop_listening_flag
            stop_listening_flag.set()
        except:
            pass
        
        # Stop animations
        self.stop_thinking()
        self.speaking = False
        
        print("🛑 STOP button pressed - interrupting...")

    def _create_enhanced_halo(self, size, radius, y_offset):
        """Create enhanced multi-layer halo with depth."""
        w, h = size
        img = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        cx = w // 2
        cy = h // 2 + y_offset

        # Multi-layer glow for depth
        layers = [
            {'radius_mult': 1.0, 'color': (0, 212, 255), 'alpha': 80},
            {'radius_mult': 0.7, 'color': (0, 180, 255), 'alpha': 120},
            {'radius_mult': 0.4, 'color': (100, 200, 255), 'alpha': 150},
        ]
        
        for layer in layers:
            layer_radius = int(radius * layer['radius_mult'])
            color = layer['color']
            
            for r in range(layer_radius, 0, -8):
                progress = r / layer_radius
                alpha = int(layer['alpha'] * (1 - progress))
                
                draw.ellipse(
                    (cx - r, cy - r, cx + r, cy + r),
                    fill=(*color, alpha)
                )

        return img.filter(ImageFilter.GaussianBlur(35))

    def _create_thinking_halo(self, size, radius, y_offset):
        """Create enhanced thinking halo (neural blue with purple tint)."""
        w, h = size
        img = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        cx = w // 2
        cy = h // 2 + y_offset

        # Purple-blue gradient for thinking
        layers = [
            {'radius_mult': 1.0, 'color': (157, 78, 221), 'alpha': 80},   # Purple
            {'radius_mult': 0.7, 'color': (123, 44, 191), 'alpha': 120},  # Deeper purple
            {'radius_mult': 0.4, 'color': (200, 150, 255), 'alpha': 150}, # Light purple
        ]
        
        for layer in layers:
            layer_radius = int(radius * layer['radius_mult'])
            color = layer['color']
            
            for r in range(layer_radius, 0, -8):
                progress = r / layer_radius
                alpha = int(layer['alpha'] * (1 - progress))
                
                draw.ellipse(
                    (cx - r, cy - r, cx + r, cy + r),
                    fill=(*color, alpha)
                )

        return img.filter(ImageFilter.GaussianBlur(35))

    def write_log(self, text: str):
        """Add message to chat with enhanced bubble design and avatar."""
        # Determine if it's user or AI message
        is_user = text.startswith("You:") or text.startswith("👤 You:")
        
        # Clean text
        if text.startswith("You:"):
            clean_text = text.replace("You:", "").strip()
        elif text.startswith("👤 You:"):
            clean_text = text.replace("👤 You:", "").strip()
        elif text.startswith("AI:"):
            clean_text = text.replace("AI:", "").strip()
        else:
            clean_text = text
        
        # Create message container (very compact)
        message_container = ctk.CTkFrame(
            self.chat_scroll,
            fg_color="transparent",
            corner_radius=0
        )
        message_container.pack(fill="x", pady=5, padx=8)
        
        if is_user:
            # User message - Neural blue gradient, right-aligned
            bubble_frame = ctk.CTkFrame(
                message_container,
                fg_color="transparent"
            )
            bubble_frame.pack(side="right", anchor="e")
            
            # User avatar (very small)
            avatar_container = ctk.CTkFrame(
                bubble_frame,
                fg_color=self.colors['bg_card'],
                corner_radius=14,
                width=28,
                height=28,
                border_width=1,
                border_color=self.colors['accent']
            )
            avatar_container.pack(side="right", padx=(5, 0))
            avatar_container.pack_propagate(False)
            
            avatar = ctk.CTkLabel(
                avatar_container,
                text="👤",
                font=("Segoe UI", 12)
            )
            avatar.pack(expand=True)
            
            # Message bubble with accent color (compact)
            bubble = ctk.CTkFrame(
                bubble_frame,
                fg_color=self.colors['accent'],
                corner_radius=14,
                border_width=0
            )
            bubble.pack(side="right", padx=(0, 5))
            
            label = ctk.CTkLabel(
                bubble,
                text=clean_text,
                font=("SF Pro Text", 11),
                text_color="#FFFFFF",
                wraplength=500,
                justify="left",
                anchor="w"
            )
            label.pack(padx=12, pady=7)
            
        else:
            # AI message - Card background with accent border, left-aligned
            bubble_frame = ctk.CTkFrame(
                message_container,
                fg_color="transparent"
            )
            bubble_frame.pack(side="left", anchor="w")
            
            # AI Avatar with glow effect (very small)
            avatar_container = ctk.CTkFrame(
                bubble_frame,
                fg_color=self.colors['bg_card'],
                corner_radius=14,
                width=28,
                height=28,
                border_width=1,
                border_color=self.colors['accent']
            )
            avatar_container.pack(side="left", padx=(0, 5))
            avatar_container.pack_propagate(False)
            
            avatar = ctk.CTkLabel(
                avatar_container,
                text="K",
                font=("SF Pro Display", 12, "bold"),
                text_color=self.colors['accent']
            )
            avatar.pack(expand=True)
            
            # Message bubble with premium styling (compact)
            bubble = ctk.CTkFrame(
                bubble_frame,
                fg_color=self.colors['bg_card'],
                corner_radius=14,
                border_width=1,
                border_color=self.colors['accent_dim']
            )
            bubble.pack(side="left")
            
            label = ctk.CTkLabel(
                bubble,
                text=clean_text,
                font=("SF Pro Text", 11),
                text_color=self.colors['text_primary'],
                wraplength=500,
                justify="left",
                anchor="w"
            )
            label.pack(padx=12, pady=7)
        
        # Smooth auto-scroll
        self.root.after(50, lambda: self.chat_scroll._parent_canvas.yview_moveto(1.0))
        
        self.message_count += 1
    
    def _animate_message(self, widget, start_alpha=0.3, target_alpha=1.0, steps=10):
        """Smooth fade-in animation for new messages."""
        widget.lift()

    def _start_typing(self):
        """Deprecated - keeping for compatibility."""
        pass

    def start_speaking(self):
        """Start speaking animation."""
        self.speaking = True
        self.thinking = False
        self.stop_thinking()  # Ensure thinking animation stops

    def stop_speaking(self):
        """Stop speaking animation."""
        self.speaking = False

    def start_thinking(self):
        """Start enhanced thinking animation with particles."""
        self.thinking = True
        self.speaking = False
        self.thinking_active = True
        self.thinking_frame_count = 0
        
        # Show thinking indicator
        self.thinking_canvas.pack()
        self._animate_thinking_particles()
    
    def _animate_thinking_particles(self):
        """Animate floating particles for thinking indicator."""
        if not self.thinking_active:
            return
        
        self.thinking_canvas.delete('all')
        
        # Canvas dimensions (updated to match larger size)
        width = 250
        height = 70
        center_x, center_y = width // 2, height // 2 - 5  # Slightly higher
        radius = 22  # Slightly larger orbit
        
        # Create 3 orbiting particles with PINK glow
        for i in range(3):
            angle = (self.thinking_frame_count + i * 120) * 0.05
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            
            # Particle size varies with position
            size = 6 + 3 * math.sin(angle)
            
            # PINK Glow effect (multiple circles)
            for r in range(int(size * 3), 0, -2):
                alpha_val = int(40 * (1 - r / (size * 3)))
                # Pink color: #FF1493 (Deep Pink)
                color_hex = f"#{255:02x}{20:02x}{147:02x}"
                
                self.thinking_canvas.create_oval(
                    x - r, y - r, x + r, y + r,
                    fill=color_hex,
                    outline='',
                    stipple='gray50'
                )
            
            # Solid core particle - BRIGHT PINK
            self.thinking_canvas.create_oval(
                x - size, y - size,
                x + size, y + size,
                fill='#FF1493',  # Deep Pink
                outline=''
            )
        
        # Animated text with pulse - LARGER and MORE VISIBLE
        alpha = int(255 * (0.6 + 0.4 * math.sin(self.thinking_frame_count * 0.1)))
        text_color = f"#{alpha:02x}{alpha:02x}{alpha:02x}"
        self.thinking_canvas.create_text(
            center_x, center_y + 30,
            text="Processing...",
            font=("SF Pro Text", 12, "bold"),  # LARGER font
            fill=text_color
        )
        
        self.thinking_frame_count += 1
        self.root.after(30, self._animate_thinking_particles)

    def stop_thinking(self):
        """Stop thinking animation."""
        self.thinking = False
        self.thinking_active = False
        self.thinking_canvas.pack_forget()
        self.thinking_canvas.delete('all')

    def _animate(self):
        """Main animation loop for face and halo."""
        now = time.time()

        # Update target values based on state
        if now - self.last_target_time > (0.25 if self.speaking else 0.7):
            if self.speaking:
                self.target_scale = random.uniform(1.02, 1.1)
                self.target_halo_alpha = random.randint(120, 150)
            elif self.thinking:
                self.target_scale = random.uniform(1.008, 1.025)
                self.target_halo_alpha = random.randint(90, 110)
            else:
                self.target_scale = random.uniform(1.004, 1.012)
                self.target_halo_alpha = random.randint(60, 80)

            self.last_target_time = now

        # Smooth interpolation
        scale_speed = 0.45 if self.speaking else 0.25
        halo_speed = 0.40 if self.speaking else 0.25

        self.scale += (self.target_scale - self.scale) * scale_speed
        self.halo_alpha += (self.target_halo_alpha - self.halo_alpha) * halo_speed

        # Create frame
        frame = Image.new("RGBA", self.size, (int(self.colors['bg_primary'][1:3], 16), 
                                                int(self.colors['bg_primary'][3:5], 16), 
                                                int(self.colors['bg_primary'][5:7], 16), 255))

        # Select halo based on state
        if self.thinking:
            halo = self.thinking_halo_base.copy()
        else:
            halo = self.halo_base.copy()
        
        halo.putalpha(int(self.halo_alpha))
        frame.alpha_composite(halo)

        # Scale face
        w, h = self.size
        face = self.face_base.resize(
            (int(w * self.scale), int(h * self.scale)),
            Image.LANCZOS
        )

        # Center face
        fx = (w - face.size[0]) // 2
        fy = (h - face.size[1]) // 2
        frame.alpha_composite(face, (fx, fy))

        # Update canvas
        img = ImageTk.PhotoImage(frame)
        self.canvas.delete("all")
        self.canvas.create_image(w // 2, h // 2, image=img)
        self.canvas.image = img

        # Continue animation loop (60 FPS)
        self.root.after(16, self._animate)