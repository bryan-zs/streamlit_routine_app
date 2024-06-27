import pytz
import pandas as pd
import altair as alt
import streamlit as st
from altair import Chart
from typing import List, Union
from pymongo import collection
from datetime import datetime, timedelta


def get_local_current_datetime() -> datetime:
    """Get datetime now in local timezone.

    Returns
    -------
    datetime
        local timezone current datetime.
    """
    now = datetime.now(tz=pytz.timezone('UTC'))
    my_tz = pytz.timezone('America/Lima')
    return now.astimezone(my_tz)


def get_week_range(date_: datetime = datetime.now(), local_tz: bool = True) -> List[datetime]:
    """Dada una fecha, calcula el rango de fechas de lunes a domingo.

    Parameters
    ----------
    date_ : datetime, optional
        Fecha de la que se requiere calcular su rango semanal, by default datetime.now()
    local_tz: bool, optional
        Indica si se debe utilizar la fecha y hora en la zona horaria local.

    Returns
    -------
    List[int]
        Lista con todas las fechas de lunes a domingo.
    """
    if local_tz:
        date_ = get_local_current_datetime()

    start = date_ - timedelta(days=date_.weekday())
    end = start + timedelta(days=6)

    def get_date_range(start_date, end_date):
        for n in range(int ((end_date - start_date).days)+1):
            yield start_date + timedelta(n)

    date_range = get_date_range(start, end)

    return list(date_range)


def validate_date(bonita_week: collection, bonita_duties: collection) -> None:
    db_date = [d for d in bonita_week.find()][0]
    now = get_local_current_datetime()
    if now > db_date['current_week']['end_week']:
        clean = bonita_duties.update_many(
                    {},
                    {'$set': {
                        'completed': [False for _ in range(7)],
                        }
                    }
                )
        if clean.acknowledged:
            week_range_dates = get_week_range()
            new_week = bonita_week.update_one(
                {},
                {'$set': {
                    'current_week': {
                        'start_week': week_range_dates[0].replace(hour=0, minute=0),
                        'end_week': week_range_dates[-1].replace(hour=0, minute=0),
                        }
                    }
                }
            )
            if new_week.acknowledged:
                print('Yes')
        else:
            validate_date(bonita_week, bonita_duties)


def make_donut(input_response: Union[int, float]) -> Chart:
    chart_color = ['#27AE60', '#12783D']
    outer_size = 120
    inner_radius = 40
    font_size = 30
    font_weigth = 700

    source = pd.DataFrame({
                'name': ['', 'arc_name'],
                '% progress': [input_response, 100-input_response]
            })

    plot = alt.Chart(source).mark_arc(innerRadius=inner_radius).encode(
                theta='% progress',
                color=alt.Color('name:N',
                                scale=alt.Scale(
                                    domain=['', 'arc_name'],
                                    range=chart_color),
                                legend=None),
                tooltip=alt.value(None)
            ).properties(width=outer_size, height=outer_size)

    text = plot.mark_text(align='center', font='Lato',
                          fontSize=font_size, fontWeight=font_weigth,
                          fontStyle='italic').encode(text=alt.value(f'{input_response} %'))

    return plot + text


general_styles = """
    <style>
        .st-emotion-cache-96rroi {
            align-items:center;
            cursor: default !important;
        }

        .e1rgp0871 {
            opacity: 1 !important;
        }

        button[title="View fullscreen"] {
            display: none;
        }

        details[title="Click to view actions"] {
            display: none;
        }

        div[data-testid="stMetricValue"] {
            text-align: center;
        }
    </style>
    """


def button_day(col: st):
    return(col.markdown("""
                <style>
                    .element-container:has(#button-after-0) {
                        display: none;
                    }

                    .element-container:has(#button-after-0) + div button {
                        width: 44px;
                        height: 44px;
                        border-radius: 50%;
                        display: inline-block;
                        text-align: center;
                        line-height: 33px;
                        margin: 4px;
                        cursor: pointer;
                        border: 1px solid grey;
                        padding-top: 5px; /* Adjust for vertical alignment */
                    }

                    .element-container:has(#button-after-0) + div button:hover {
                        color: purple;
                        border-color: purple;
                    }

                    .element-container:has(#button-after-0) + div button:focus {
                        color: purple !important;
                        border-color: purple !important;
                        box-shadow: purple 0 0 0 .2rem;
                    }

                    .element-container:has(#button-after-0) + div button:active {
                        background-color: transparent !important;
                    }
                </style>
            """, unsafe_allow_html=True),
            col.markdown(f'<div id="button-after-0""></div>', unsafe_allow_html=True))


def button_today(col: st):
    return(col.markdown("""
                <style>
                    .element-container:has(#button-after-1) {
                        display: none;
                    }

                    .element-container:has(#button-after-1) + div button {
                        width: 44px;
                        height: 44px;
                        border-radius: 50%;
                        display: inline-block;
                        text-align: center;
                        line-height: 33px;
                        margin: 4px;
                        cursor: pointer;
                        border: 1px solid grey;
                        padding-top: 5px;
                        background-color: #00C851; /* Green */
                        padding: 5px 7px 4px 7px !important;
                    }
                    .element-container:has(#button-after-1) + div button:hover {
                        color: purple;
                        border-color: purple;
                    }
                    .element-container:has(#button-after-1) + div button:focus {
                        color: purple !important;
                        border-color: purple !important;
                        box-shadow: purple 0 0 0 .2rem;
                    }
                </style>
            """, unsafe_allow_html=True),
            col.markdown(f'<div id="button-after-1""></div>', unsafe_allow_html=True))


def button_color_picker(columna: st, color: str, ix_o: str):
    return(columna.markdown(f"""
        <style>
            .element-container:has(#button-after-o_{ix_o}) {{
                display: none;
            }}

            .element-container:has(#button-after-o_{ix_o}) + div {{
                text-align: center;
                align-items: center !important;
            }}

            .element-container:has(#button-after-o_{ix_o}) + div button {{
                background-color: {color} !important;
                color: {color} !important;
            }}
        </style>
    """, unsafe_allow_html=True),
    columna.markdown(f'<div id="button-after-o_{ix_o}"></div>',
                     unsafe_allow_html=True))


def input_text(c1:st, color: str):
    return(c1.markdown(f"""
        <style>
            .element-container:has(#button-after-ph) {{
                display: none;
            }}

            .element-container:has(#button-after-ph) + div input {{
                /* background-color: rgb(240, 242, 246); */
                background-color: {color};
            }}
        </style>
    """, unsafe_allow_html=True),
    c1.markdown(f'<div id="button-after-ph"></div>', unsafe_allow_html=True))


def button_submit(c2: st, color: str):
    return(c2.markdown(f"""
        <style>
            .element-container:has(#button-after-2) {{
                display: none;
            }}

            .element-container:has(#button-after-2) + div button {{
                background-color: {color} !important;
                border-color: {color}
                /* padding-top: 3px !important; */
                /* margin-top: 13px; */
                align-items: center;
                justify-content: center;
                font-weight: 800 !important;
            }}

            .row-widget {{
                width: auto !important;
            }}

            .e10yg2by2 {{
                justify-content: center !important;
            }}
        </style>
    """, unsafe_allow_html=True),
    c2.markdown(f'<div id="button-after-2"></div>', unsafe_allow_html=True))


def button_edit_del_cat(tc_3: st):
    return(st.markdown(
        """
            <style>
                .element-container:has(#button-after-z1) {
                    display: none;
                }

                .element-container:has(#button-after-z1) + div button {
                    border: 0px;
                    padding-top: 0px;
                }
            </style>
        """, unsafe_allow_html=True),
        tc_3.markdown('<div id="button-after-z1"></div>',
                      unsafe_allow_html=True))


def button_edit_del_act(stc2: st):
    return(st.markdown("""
        <style>
            .element-container:has(#button-after-z2) {
                display: none;
            }

            .element-container:has(#button-after-z2) + div button {
                border: 0px;
                padding-top: 0px;
            }
        </style>
    """, unsafe_allow_html=True),
    stc2.markdown('<div id="button-after-z2"></div>', unsafe_allow_html=True))
