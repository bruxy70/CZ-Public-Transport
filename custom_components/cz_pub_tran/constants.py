"""
Text constants for cz_pub_tran sensor
"""

CONNECTION_DETAIL_HEADER = {
    'text': '',
    'list': '',
    'HTML': '<table>\n'
            '<tr>'
            '<th align="left">Line</th>'
            '<th align="left">Departure</th>'
            '<th align="left">From</th>'
            '<th align="left">Arrival</th>'
            '<th align="left">To</th>'
            '<th align="left">Delay</th>'
            '</tr>'
}

CONNECTION_DETAIL_LINE_DELAY = {
    'text': '{:<4} {:<5} ({}) -> {:<5} ({})   !!! {}min delayed',
    'list': '{:<4} {:<5} ({}) -> {:<5} ({})   !!! {}min delayed',
    'HTML': '<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}min</td></tr>'
}

CONNECTION_DETAIL_LINE_NO_DELAY = {
    'text': '{:<4} {:<5} ({}) -> {:<5} ({})',
    'list': '{:<4} {:<5} ({}) -> {:<5} ({})',
    'HTML': '<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td></td></tr>'
}

CONNECTION_DETAIL_FOOTER = {
    'text': '',
    'list': '',
    'HTML': '</table>'
}