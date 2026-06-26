import flet as ft


def convert_amharic_to_latin(text: str) -> str:
    """
    Convert Amharic text to Latin sound representation.
    Non-Amharic characters are left unchanged.
    
    Args:
        text: String containing Amharic text
        
    Returns:
        String with Amharic characters transliterated to Latin
    """
    import unicodedata
    
    # Transliteration mapping
    base_consonants = {
        'ሀ': 'h', 'ለ': 'l', 'ሐ': 'h', 'መ': 'm', 'ሠ': 's',
        'ረ': 'r', 'ሰ': 's', 'ሸ': 'sh', 'ቀ': 'q', 'በ': 'b',
        'ተ': 't', 'ቸ': 'ch', 'ኀ': 'h', 'ነ': 'n', 'ኘ': 'ny',
        'አ': 'ə', 'ከ': 'k', 'ኸ': 'h', 'ወ': 'w', 'ዐ': 'ə',
        'ዘ': 'z', 'ዠ': 'zh', 'የ': 'y', 'ደ': 'd',
        'ጀ': 'j', 'ገ': 'g', 'ጠ': 't', 'ጨ': 'ch',
        'ጰ': 'p', 'ጸ': 'ts', 'ፀ': 'ts', 'ፈ': 'f', 'ፐ': 'p',
    }
    
    vowel_suffixes = ['a', 'u', 'i', 'a', 'e', '', 'o']
    
    # Build the full mapping
    amharic_to_sound = {}
    for first_order_char, cons in base_consonants.items():
        base_code = ord(first_order_char)
        for order in range(7):
            char_code = base_code + order
            if 0x1200 <= char_code <= 0x137F:
                syllable = chr(char_code)
                try:
                    name = unicodedata.name(syllable)
                    if 'ETHIOPIC' not in name:
                        continue
                except (ValueError, TypeError):
                    continue
                sound = cons + vowel_suffixes[order]
                amharic_to_sound[syllable] = sound
    
    # Labiovelars and extras
    extra_mapping = {
        'ቈ': 'qwa', 'ቊ': 'qwi', 'ቋ': 'qwa', 'ቌ': 'qwe', 'ቍ': 'qw',
        'ኈ': 'hwa', 'ኊ': 'hwi', 'ኋ': 'hwa', 'ኌ': 'hwe', 'ኍ': 'hw',
        'ዀ': 'hwa', 'ዂ': 'hwi', 'ዃ': 'hwa', 'ዄ': 'hwe',
        'ጐ': 'gwa', 'ጒ': 'gwi', 'ጓ': 'gwa', 'ጔ': 'gwe', 'ጕ': 'gw',
    }
    amharic_to_sound.update(extra_mapping)
    
    # Convert the text
    result = []
    for ch in text:
        result.append(amharic_to_sound.get(ch, ch))
    return ''.join(result)


def main(page: ft.Page):
    page.title = "Amharic → Latin Converter"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO
    
    # Input text field
    input_text = ft.TextField(
        label="Amharic Text",
        hint_text="Enter Amharic text here...",
        multiline=True,
        min_lines=3,
        max_lines=10,
        expand=True,
        border_radius=10,
    )
    
    # Output text field (read-only)
    output_text = ft.TextField(
        label="Latin Transliteration",
        hint_text="Transliterated text will appear here...",
        multiline=True,
        min_lines=3,
        max_lines=10,
        expand=True,
        read_only=True,
        border_radius=10,
        border_color=ft.Colors.GREEN_400,
    )
    
    # Status text
    status_text = ft.Text("", italic=True, color=ft.Colors.GREY_600)
    
    # Character counter
    char_counter = ft.Text("0 characters", size=12, color=ft.Colors.GREY_600)
    
    def convert_text(e):
        """Convert the input text and update the output."""
        text = input_text.value or ""
        if text.strip():
            try:
                result = convert_amharic_to_latin(text)
                output_text.value = result
                status_text.value = f"✓ Converted {len(text)} characters → {len(result)} characters"
                status_text.color = ft.Colors.GREEN_700
                page.update()
            except Exception as err:
                status_text.value = f"✗ Error: {str(err)}"
                status_text.color = ft.Colors.RED_700
                page.update()
        else:
            output_text.value = ""
            status_text.value = "Please enter some text to convert"
            status_text.color = ft.Colors.GREY_600
            page.update()
    
    def clear_text(e):
        """Clear both input and output."""
        input_text.value = ""
        output_text.value = ""
        status_text.value = ""
        char_counter.value = "0 characters"
        page.update()
    
    def copy_output(e):
        """Copy the output text to clipboard."""
        if output_text.value:
            page.set_clipboard(output_text.value)
            status_text.value = "✓ Copied to clipboard!"
            status_text.color = ft.Colors.GREEN_700
            page.update()
    
    def update_char_count(e):
        """Update the character counter."""
        text = input_text.value or ""
        char_counter.value = f"{len(text)} characters"
        page.update()
    
    # Attach the character counter update
    input_text.on_change = update_char_count
    
    # Button row
    buttons = ft.Row(
        [
            ft.ElevatedButton(
                "Convert →",
                icon=ft.Icons.TRANSLATE,
                on_click=convert_text,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.BLUE_700,
                    color=ft.Colors.WHITE,
                ),
            ),
            ft.OutlinedButton(
                "Clear",
                icon=ft.Icons.CLEAR,
                on_click=clear_text,
            ),
            ft.OutlinedButton(
                "Copy",
                icon=ft.Icons.COPY,
                on_click=copy_output,
            ),
        ],
        spacing=10,
        wrap=True,
    )
    
    # Example buttons
    examples = ft.Row(
        [
            ft.TextButton(
                "ሰላም ልጅ",
                on_click=lambda e: set_example("ሰላም ልጅ እንዴት ነህ?"),
            ),
            ft.TextButton(
                "አመሰግናለሁ",
                on_click=lambda e: set_example("አመሰግናለሁ ዛሬ ስራህ እንዴት ነው?"),
            ),
            ft.TextButton(
                "ሠላም",
                on_click=lambda e: set_example("ሠላም ወደ ኢትዮጵያ"),
            ),
        ],
        spacing=5,
        wrap=True,
    )
    
    def set_example(text):
        """Set an example text in the input field and convert it."""
        input_text.value = text
        char_counter.value = f"{len(text)} characters"
        convert_text(None)
    
    # Build the layout
    page.add(
        ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.TRANSLATE, size=30, color=ft.Colors.BLUE_700),
                            ft.Text(
                                "Amharic → Latin Converter",
                                size=30,
                                weight=ft.FontWeight.BOLD,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Divider(height=20, thickness=2),
                    ft.Text(
                        "Enter Amharic text below and click 'Convert' to transliterate to Latin",
                        size=14,
                        color=ft.Colors.GREY_700,
                        italic=True,
                    ),
                    ft.Text("Examples:", size=12, weight=ft.FontWeight.BOLD),
                    examples,
                    ft.Divider(height=10),
                    input_text,
                    ft.Row(
                        [char_counter, ft.Container(expand=True)],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    buttons,
                    output_text,
                    status_text,
                ],
                spacing=15,
            ),
            expand=True,
        )
    )


ft.app(main)