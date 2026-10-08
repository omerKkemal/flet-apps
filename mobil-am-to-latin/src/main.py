import flet as ft


def build_mapping() -> dict:
    """Build the Amharic (Ethiopic) -> Latin syllable mapping once."""
    # First-order character of each consonant series -> Latin consonant
    base_consonants = {
        'ሀ': 'h', 'ለ': 'l', 'ሐ': 'h', 'መ': 'm', 'ሠ': 's',
        'ረ': 'r', 'ሰ': 's', 'ሸ': 'sh', 'ቀ': 'q', 'ቐ': 'q',
        'በ': 'b', 'ቨ': 'v', 'ተ': 't', 'ቸ': 'ch', 'ኀ': 'h',
        'ነ': 'n', 'ኘ': 'ny', 'አ': '', 'ከ': 'k', 'ኸ': 'h',
        'ወ': 'w', 'ዐ': '', 'ዘ': 'z', 'ዠ': 'zh', 'የ': 'y',
        'ደ': 'd', 'ዸ': 'd', 'ጀ': 'j', 'ገ': 'g', 'ጘ': 'ng',
        'ጠ': 't', 'ጨ': 'ch', 'ጰ': 'p', 'ጸ': 'ts', 'ፀ': 'ts',
        'ፈ': 'f', 'ፐ': 'p',
    }

    # The 7 vowel orders: ä, u, i, a, e, ə (no vowel), o
    vowels = ['e', 'u', 'i', 'a', 'ie', '', 'o']
    # Glottal series (አ, ዐ) have no consonant, so the 1st/6th orders need a vowel
    glottal_vowels = ['e', 'u', 'i', 'a', 'ie', 'e', 'o']

    mapping = {}
    for first_char, cons in base_consonants.items():
        base_code = ord(first_char)
        suffixes = glottal_vowels if cons == '' else vowels
        for order in range(7):
            mapping[chr(base_code + order)] = cons + suffixes[order]

    # Labiovelars and extras
    mapping.update({
        'ቈ': 'qwe', 'ቊ': 'qwi', 'ቋ': 'qwa', 'ቌ': 'qwie', 'ቍ': 'qw',
        'ኈ': 'hwe', 'ኊ': 'hwi', 'ኋ': 'hwa', 'ኌ': 'hwie', 'ኍ': 'hw',
        'ዀ': 'kwe', 'ዂ': 'kwi', 'ዃ': 'kwa', 'ዄ': 'kwie',
        'ጐ': 'gwe', 'ጒ': 'gwi', 'ጓ': 'gwa', 'ጔ': 'gwie', 'ጕ': 'gw',
        'ኧ': 'e',
    })

    # Ethiopic punctuation
    mapping.update({
        '።': '.', '፣': ',', '፤': ';', '፥': ':', '፦': ':',
        '፧': '?', '፡': ' ', '፠': '.', '፨': '.',
    })
    return mapping


AMHARIC_TO_SOUND = build_mapping()


def convert_amharic_to_latin(text: str) -> str:
    """Convert Amharic text to Latin; non-Amharic characters are unchanged."""
    return ''.join(AMHARIC_TO_SOUND.get(ch, ch) for ch in text)


def main(page: ft.Page):
    page.title = "Amharic → Latin Converter"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    input_text = ft.TextField(
        label="Amharic Text",
        hint_text="Enter Amharic text here...",
        multiline=True,
        min_lines=3,
        max_lines=10,
        border_radius=10,
    )

    output_text = ft.TextField(
        label="Latin Transliteration",
        hint_text="Transliterated text will appear here...",
        multiline=True,
        min_lines=3,
        max_lines=10,
        read_only=True,
        border_radius=10,
        border_color=ft.Colors.GREEN_400,
    )

    status_text = ft.Text("", italic=True, color=ft.Colors.GREY_600)
    char_counter = ft.Text("0 characters", size=12, color=ft.Colors.GREY_600)

    def convert_text(e=None):
        text = input_text.value or ""
        if text.strip():
            try:
                result = convert_amharic_to_latin(text)
                output_text.value = result
                status_text.value = (
                    f"✓ Converted {len(text)} characters → {len(result)} characters"
                )
                status_text.color = ft.Colors.GREEN_700
            except Exception as err:
                status_text.value = f"✗ Error: {err}"
                status_text.color = ft.Colors.RED_700
        else:
            output_text.value = ""
            status_text.value = "Please enter some text to convert"
            status_text.color = ft.Colors.GREY_600
        page.update()

    def clear_text(e):
        input_text.value = ""
        output_text.value = ""
        status_text.value = ""
        char_counter.value = "0 characters"
        page.update()

    async def copy_output(e):
        if output_text.value:
            await ft.Clipboard().set(output_text.value)
            status_text.value = "✓ Copied to clipboard!"
            status_text.color = ft.Colors.GREEN_700
        else:
            status_text.value = "Nothing to copy yet"
            status_text.color = ft.Colors.GREY_600
        page.update()

    def update_char_count(e):
        char_counter.value = f"{len(input_text.value or '')} characters"
        page.update()

    input_text.on_change = update_char_count

    def set_example(text):
        input_text.value = text
        char_counter.value = f"{len(text)} characters"
        convert_text()

    buttons = ft.Row(
        [
            ft.Button(
                content="Convert →",
                icon=ft.Icons.TRANSLATE,
                on_click=convert_text,
                bgcolor=ft.Colors.BLUE_700,
                color=ft.Colors.WHITE,
            ),
            ft.OutlinedButton(
                content="Clear",
                icon=ft.Icons.CLEAR,
                on_click=clear_text,
            ),
            ft.OutlinedButton(
                content="Copy",
                icon=ft.Icons.COPY,
                on_click=copy_output,
            ),
        ],
        spacing=10,
        wrap=True,
    )

    examples = ft.Row(
        [
            ft.TextButton(
                content="ሰላም ልጅ",
                on_click=lambda e: set_example("ሰላም ልጅ እንዴት ነህ?"),
            ),
            ft.TextButton(
                content="አመሰግናለሁ",
                on_click=lambda e: set_example("አመሰግናለሁ ዛሬ ስራህ እንዴት ነው?"),
            ),
            ft.TextButton(
                content="ሠላም",
                on_click=lambda e: set_example("ሠላም ወደ ኢትዮጵያ"),
            ),
        ],
        spacing=5,
        wrap=True,
    )

    page.add(
        ft.Column(
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
                char_counter,
                buttons,
                output_text,
                status_text,
            ],
            spacing=15,
        )
    )


ft.run(main)