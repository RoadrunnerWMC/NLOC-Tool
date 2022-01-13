# NLOC Tool

A tool for converting NLOC (".loc") localization files from *Luigi's Mansion:
Dark Moon* and *Punch-Out!!* (and maybe other games, too) to/from text files.
It also supports NLOC files embedded in .dict/.data archives.

## License

GNU GPL v3. See the "LICENSE" file for more information.

## Documentation

### NLOC Tool

Run `nloc_tool.py` with Python 3. Use `-h` or `--help` to see specific usage
information.

Note: For convenience, NLOC Tool will use hash keys from
`plaintext_hash_keys.txt` when converting to NLOCT. If you find additional hash
keys, add them to the file and send a PR!

### NLOC file specification

"NLOC" probably means "Next level LOCalization". (Next Level Games is the
development studio, and if you ask LMDM to display a message with a nonexistent
ID, it uses the string "missing loc string" as a default/fallback, which
probably means they use "loc" to mean "localized"/"localization".)

NLOC files don't have file extensions in *Luigi's Mansion: Dark Moon*, because
they're embedded in .dict/.data archives that strip filenames. They use ".loc"
file extensions in *Punch-Out!!*, though, so that's the official file extension
for the format.

    Header:
        00-03    "NLOC"
        04-07    Always 1. The game code rejects files that have
                 anything other than 1 here. Probably a file format
                 version number, or maybe it defines the string
                 encoding and they only ever implemented one choice.
        08-0B    Language ID hash value. For example, for English,
                 this is the hash of the string 'english'.
        0C-0F    Number of strings
        10-13    Always 0 in LMDM, and always (?) 1 in PO. Maybe this specifies
                 the file endianness? For now, at least, NLOC Tool treats it
                 that way.

    String info table:
        (Note: entries are sorted by message ID hashes)
        00-03    Message ID hash value
        04-07    String offset, relative to the end of this table

    String data area:
        (Note: strings are not ordered in the same way as in the info
        table, but instead appear to be in whatever order NLG defined
        them in: similar strings are grouped together in locally
        logical orders.)
        Giant list of UTF-16 (UCS-2?) null-terminated text strings.

### NLOCT file specification

NLOCT (NLOC Text, ".loct" file extension) is a custom text format I designed to
make it easy to edit NLOC.

NLOCT files use UTF-8 encoding.

There are three kinds of lines: language ID lines, message lines, and comment
lines.

#### Language ID line

The language ID line starts with `langid:` and is followed by the language ID
as a hash value ("hash values" are defined in the "Message Lines" section
below). If a NLOCT has more than one language ID line for some reason, the last
one takes precedence.

Example: `langid: "english"`

#### Message lines

Message lines map a hash value to a message string.

The first thing in a message line is the hash value. The hash value can be
represented in two ways: as a hex value (e.g. `105A690D`), or as a
quote-delimited string that hashes to the desired value (e.g.
`"unlock_vault"`). Ideally strings would be used everywhere, but we don't know
the original strings for most of the messages, so we unfortunately have to use
the raw hex values most of the time.

After the hash value and at least one space character is the message string.
See the "Message String Format" section for details on how to write message
strings.

The order in which messages are defined in the file corresponds to their order
in the NLOC's string table, unless `--sort` is used when running the converter.

Examples:

    "unlock_vault"    Complete the first mission{p}in the Gloomy Manor to{p}unlock E. Gadd's Vault!
    4196E04           {tp:0.01}Rescue the Toad in the Jungle Exhibit.{/tp}

#### Comment lines

Comment lines start with a "`#`", and obviously do nothing. Completely blank
lines are also comments.

You can also make block comments, starting and ending with "`###`". Every line
between them is treated as a comment.

Examples:

    # This is a comment.

    ###
    This is a block comment.
    ###

### Message string format (NLOC and NLOCT)

NLOCs use a fairly simple markup system.

#### Tags

##### {p}

Line break. This tag is self-closing.

*Availability: Punch-Out!!, Luigi's Mansion: Dark Moon*

##### {0}, {1}, {2}, ...

Format string parameters. The game will replace these with values calculated at
runtime. The specific meaning changes depending on context. These tags are
self-closing.

*Availability: Punch-Out!!, Luigi's Mansion: Dark Moon*

##### {tp}

"Text pace." This sets the speed at which text is printed to the screen. It
takes a parameter: the amount of time to wait between printing characters, in
seconds. (Example: `{tp:0.01}`.) It is closed with `{/tp}`.

Multiple `{tp}` tags can be used in a single line to create text that prints at
varying speeds.

*Availability: Luigi's Mansion: Dark Moon*

##### {ts}

"Text size." This sets the size of text. It takes a parameter: the size
relative to the standard font size. (Example: `{ts:1.5}`.) It is closed with
`{/ts}`.

These tags must always be applied to an entire line of text, or else behavior
is buggy. Very large values (such as 8) can cause softlocks.

*Availability: Luigi's Mansion: Dark Moon*

##### {clr}

"Color." This sets the color of the text. It takes a parameter: the color in
6-digit RGB hexadecimal format. (Example: `{clr:0248AC}`.) It is closed with
`{clr:pop}`.

Multiple `{clr}` tags can be used on different parts of a line of text.

*Availability: Punch-Out!!, Luigi's Mansion: Dark Moon*

##### {vs}, {rb}, {rt}, {hs}

Unknown; used in the Japanese translation. TODO: research

#### Special characters

These are specific to individual games.

##### Punch-Out!!

    =: Seems to represent different controller buttons depending on context?

##### Luigi's Mansion: Dark Moon

    ɣ: X button
    ɏ: Y button
    ɐ: A button
    ɓ: B button
    ɭ: L button
    ɹ: R button
    ʘ: Circle pad
    א: Start button
    ڠ: Home button (does not work in bunker scripts)
    Ѡ: (Super) Poltergust
    ʣ: Dark light level 2
    ʤ: Dark light level 3
    қ: Power gauge level 2 (green)
    Җ: Power gauge level 3 (red)
    ⱷ: Silver money bag with "G" (does not work in bunker scripts)
    ♡: Heart icon (does not work in bunker scripts)
    ₢: Greenie icon (does not work in bunker scripts)
    Ԇ: Key icon (does not work in bunker scripts)
    Ɠ: Golden money bag with "G"
    ƃ: Silver money bag with "G"

#### List of text colors used in LMDM

Below is a list of all uses of various text colors, in both the "english" and
"ukenglish" localizations. Lowercased, whitespace-stripped, sorted, and
deduplicated. Should be helpful when picking colors for custom messages.

##### 51E949

"", "baby luigi", "gi", "i", "igi", "l", "lu", "luigi", "uigi"

##### 71D2FF

"", "a-1", "a-2", "a-3", "a-4", "a-5", "b-1", "b-2", "b-3",
"b-4", "b-5", "c-1", "c-2", "c-3", "c-4", "c-5", "clock",
"clock hands", "crank", "d-1", "d-2", "d-3",
"dark-light device", "double-yoos", "ds", "dual scream",
"e-1", "e-2", "e-3", "e-4", "e-5", "e-gates", "flashlight",
"front door key", "front-door key", "g", "gears", "gen",
"generator", "green circular panel", "green circular panels",
"hour hand", "key", "keys", "lator", "lift", "lshifter",
"minute hand", "nerator", "parasco", "parascope",
"pinwheel vanes", "pix", "pixelator", "pixelator screen",
"pixelshift screen", "pixelshifter", "poltergust",
"poltergust 5000", "portrifica", "rator", "rotor",
"scarescraper", "security camera", "security image",
"security system", "security-camera", "special",
"special compass", "special key", "strobulb", "torch",
"vane", "vanes", "water pump"

##### 98E66C

*(note: used for treasure or something)*

""

##### A554D0

"dark m", "dark moon", "oon"

##### D50000

"mar", "mario", "red"

##### D8BCE6

"", "baboon", "big boo", "boo", "boo b. trap", "boo boo",
"boo-boo", "boodonkulous", "boofoon", "booger",
"boogie woogie", "booillon", "boolean", "boolldog", "booluga",
"boony raboot", "boopa troopa", "booreaucrat", "boos",
"bootine", "boouncer", "combooter", "french boodle",
"jamboolaya", "king boo", "mamboo", "maraboo", "ooga booga",
"paraboola", "paranormal"

##### E06F00

"vault"

##### E64A39

"red coin"

##### F0DE8A

*(note: used for multiplayer treasure or something)*

""

##### FF9754

"", "ater supply", "b", "bunker", "cellar", "chalet",
"clock tower", "clock tower gate", "clockworks court",
"courtyard", "crypt", "crystal quarry", "dining room",
"drafting office", "drafting room", "evershade valley",
"fishing hut", "foyer", "front", "front entrance", "g",
"garage", "gardener's lab", "gloomy manor", "gondola",
"haunted", "haunted towers", "hollow tree", "hydro generator",
"ice age exhibit", "inner courtyard", "jungle exhibit", "ker",
"ks", "lab", "library", "main", "main hall", "maint",
"mainten", "nance", "nce", "ndola", "old clockw",
"old clockworks", "rkshop", "rooftop pool", "room",
"roundhouse", "secret mine", "service elevator",
"service lift", "space exhibit", "station", "storage room",
"synchronisation lab", "synchronization room", "terminal",
"terrace", "thrill tower", "train exhibit",
"treacherous mansion", "tree house", "vault", "w",
"warehouse", "water supply", "workshop"

##### FFFCFC

*(note: ...TCRF material?)*

""