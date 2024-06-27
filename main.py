import time
import pymongo
# import certifi
import streamlit as st
from datetime import datetime
from utils import get_week_range, validate_date, make_donut,\
                  general_styles, button_day, button_today,\
                  button_color_picker, input_text, button_submit,\
                  button_edit_del_cat, button_edit_del_act


st.set_page_config(layout='centered', page_title='Rutina Bonita')

st.markdown('''
        <h1
            align="center"
            style="color:#8532C5;"
        >
            Rutina Bonita
        </h1>
    ''', unsafe_allow_html=True)

list_tabs: list[str] = ['Actividades', 'Análisis', 'Gestionar']
whitespace: int = 33
tab1, tab2, tab3 = st.tabs([s.center(whitespace,'\u2000') for s in list_tabs])

st.markdown(general_styles, unsafe_allow_html=True)

@st.cache_resource
def init_connection():
    print('Reload connection')
    # ca = certifi.where()
    connection_string = st.secrets['mongo']['connect']
    return pymongo.MongoClient(connection_string)#, tlsCAFile=ca)

client = init_connection()
bonita_db = client['bonita_db']

bonita_week = bonita_db['date']
bonita_routine = bonita_db['routine']
bonita_duties = bonita_db['duties']

#################
#               #
# VALIDATE DATE #
#               #
#################

validate_date(bonita_week, bonita_duties)


##################
#                #
# BUILD LOCAL DB #
#                #
##################

db_routine = bonita_routine.find()
db_duties = bonita_duties.find()

db: dict = dict()
activities: dict = dict()
j: int = 0
for i, routine in enumerate(db_routine):
    for actvd in bonita_duties.find({'category_id': routine['_id']}):
        routine['tasks'].append({'id': actvd['_id'],
                                 'name': actvd['name'],
                                 'completed': actvd['completed']})
        activities[j] = actvd
        j += 1
    db[i] = routine


with tab1:
    # Initialize the key in session state
    if 'clicked' not in st.session_state:
        st.session_state['clicked'] = [False for _ in range(7)]
    if 'daily_progress' not in st.session_state:
        st.session_state['daily_progress'] = [False for _ in range(7)]

    week_range_dates = get_week_range()
    week_range = [week_day.day for week_day in week_range_dates]
    days = ['L', 'M', 'M', 'J', 'V', 'S', 'D']
    days_names = [f'{d[0]}{d[1]}' for d in list(zip(week_range, days))]
    today = datetime.now().day
    n_today = datetime.now().weekday()

    _, _, col1, col2, col3, col4, col5, col6, col7, _, _ = st.columns(11)
    cols = [col1, col2, col3, col4, col5, col6, col7]

    def load_day(day_):
        st.session_state['clicked'] = [False for _ in range(7)]
        st.session_state['clicked'][day_-1] = True
        st.session_state['selected_day'] = day_
        st.session_state['daily_progress'] = [tarea['completed'][day_-1] for tarea in activities.values()]

    ##############
    #            #
    # DAY PICKER #
    #            #
    ##############

    for day, col in enumerate(cols):
        if week_range[day] != today:
            button_day(col)
            col.button(f'{week_range[day]} {days[day]}',
                       key=f'{days[day]}_{day+1}',
                       on_click=load_day,
                       args=(day+1,))
        else:
            button_today(col)
            col.button(f'{week_range[day]} Hoy',
                       key=f'{days[day]}_{day+1}',
                       on_click=load_day,
                       args=(day+1,))
            selected_day = day+1
            if 'selected_day' not in st.session_state:
                st.session_state['selected_day'] = selected_day

    def update_progress(actv_id, sel_day):
        progress = [a['completed'] for a in activities.values() if a['_id']==actv_id][0]
        progress[sel_day-1] = not progress[sel_day-1]
        st.session_state['daily_progress'] = [tarea['completed'][sel_day-1] for tarea in activities.values()]
        update_act = bonita_duties.update_one({'_id': actv_id},
                                              {'$set': {
                                                  'completed': progress
                                              }})
        if update_act.acknowledged:
            print('Updated act successfully!')

    tab1.subheader(f'_{week_range_dates[st.session_state["selected_day"]-1].date()}_:')

    ############
    #          #
    #  GRILLA  #
    #          #
    ############

    for catg in db.values():
        tupper = tab1.container(border=True)
        _, tc1, tc2, _, tc_3, _ = tupper.columns([2,1,3,1,2,1])

        tc1.color_picker(label=f"category_color_{catg['color']}",
                         label_visibility='collapsed',
                         disabled=True,
                         value=catg['color'])

        tc2.write(catg['category'])

        for day_key, day_value in enumerate(catg['tasks']):
            sub_tupper = tupper.container(border=False)
            _, stc1, stc2, _ = sub_tupper.columns([5,4,3,2])
            stc1.write(day_value['name'])
            stc2.checkbox(
                label=f"cb_{st.session_state['selected_day']}_{str(day_value['id'])[-5:]}",
                key=f"cb_{st.session_state['selected_day']}_{str(day_value['id'])[-5:]}",
                value=day_value['completed'][st.session_state['selected_day']-1],
                label_visibility='collapsed',
                on_change=update_progress,
                args=(day_value['id'], st.session_state['selected_day'])
            )


    if False not in st.session_state['daily_progress']:
        tab1.balloons()


with tab2:
    array_cols = [5,1,1,1,1,1,1,1]
    num_cols = len(array_cols)
    boxes: dict = {0: [[]]}
    ix: int = 1
    done_today: int = 0
    for category in db.values():
        for task in category['tasks']:
            name = [task['name']]
            colors = [category['color'] if i==True else '#FFFFFF' for i in task['completed']]
            done_today += task['completed'][n_today]
            row = name + colors
            boxes[ix] = row
            ix += 1
    num_rows = len(boxes)


    ############
    #          #
    # MÉTRICAS #
    #          #
    ############

    tab2.subheader('_Objetivo diario:_')
    t2c1, t2c2, t2c3 = tab2.columns(3)

    with t2c1.container(border=True):
        st.metric('Tareas Realizadas:', done_today)

    percentage_today = int((done_today/len(activities))*100)

    donut_chart = make_donut(percentage_today)
    _, t2c2c, _ = t2c2.columns([1,2,2])
    t2c2c.altair_chart(donut_chart)

    with t2c3.container(border=True):
        st.metric('Total de actividades:', len(activities))


    ############
    #          #
    #  GRILLA  #
    #          #
    ############

    cols_boxes = [tab2.columns(array_cols) for _ in range(num_rows)]

    for i in range(num_rows):
        for j in range(num_cols):
            if i==j==0:
                pass
            elif i==0 and j>0: # days of week
                cols_boxes[i][j].markdown("""
                    <style>
                        .element-container:has(#button-after-x) {
                            display: none;
                        }

                        .element-container:has(#button-after-x) + div button {
                            cursor: default;
                            border: 0px;
                            color: black;
                            background-color: white;
                        }
                    </style>
                """, unsafe_allow_html=True)
                cols_boxes[i][j].markdown(f'<div id="button-after-x""></div>',
                                          unsafe_allow_html=True)

                if today==week_range[j-1]:
                    cols_boxes[i][j].button(f'**{days_names[j-1]}**',
                                            key=days_names[j-1],
                                            disabled=True)
                else:
                    cols_boxes[i][j].button(f'{days_names[j-1]}',
                                            key=days_names[j-1],
                                            disabled=True)
            elif i!=0 and j==0: # tasks
                cols_boxes[i][j].write(boxes[i][j])
            else: # colored boxes
                cols_boxes[i][j].color_picker(label=f"{i}/{j}",
                                              value=boxes[i][j],
                                              label_visibility='collapsed',
                                              disabled=True)


with tab3:
    #################################
    #                               #
    # Agregar categoría o actividad #
    #                               #
    #################################

    # Initialize the key in session state
    if 'category_color' not in st.session_state:
        st.session_state['category_color'] = 0
    if 'loaded_category' not in st.session_state:
        st.session_state['loaded_category'] = ''
    if 'add_cat_or_act' not in st.session_state:
        st.session_state['add_cat_or_act'] = False


    def reset_color():
        st.session_state['category_color'] = None

    def select_color(color: str) -> None:
        st.session_state['category_color'] = None
        st.session_state['category_color'] = color

    def new_color():
        st.session_state['category_color'] = None
        st.session_state['category_color'] = st.session_state['nuevo_color']

    def load_color():
        if st.session_state['loaded_category']:
            matched_color = [val['color'] for val in db.values() if val['category']==st.session_state['loaded_category']][0]
            st.session_state['category_color'] = matched_color
        else:
            st.session_state['category_color'] = None

    def func_add_cat_or_act():
        st.session_state['add_cat_or_act'] = True


    _, pilar_2, _ = st.columns(3)

    if st.session_state['add_cat_or_act']==True:
        pilar_2.radio('Selecciona una opción para agregar:',
                      options=['Categoría', 'Actividad'],
                      index=None,
                      horizontal=True,
                      on_change=reset_color,
                      key='nuevo')

        if st.session_state['nuevo'] is not None:
            if st.session_state['nuevo']=='Categoría':
                o1, o2, o3, o4, o5, o6 = st.columns(6)
                colors = ['#FDFFB6', '#CAFFBF', '#9BF6FF', '#A0C4FF', '#FFC6FF']
                for ix_o, option in enumerate(zip([o1, o2, o3, o4, o5], colors), 1):
                    button_color_picker(option[0], option[1], ix_o)
                    option[0].button(f'l{ix_o}',
                                     key=f'option_{ix_o}',
                                     on_click=select_color,
                                     args=(option[1],))

                o6.color_picker('Nuevo color:',
                                key='nuevo_color',
                                value='#F58686',
                                on_change=new_color)

            elif st.session_state['nuevo']=='Actividad':
                _, c_b, _ = st.columns([2,3,2])
                c_b.selectbox('Selecciona la categoría',
                              [value['category'] for value in db.values()],
                              key='loaded_category',
                              index=None,
                              label_visibility='collapsed',
                              placeholder='Selecciona una categoría',
                              on_change=load_color)

    else:
        pilar_2.button('Agregar categoría o actividad',
                       key='add_new_cat_or_act',
                       on_click=func_add_cat_or_act)

    if isinstance(st.session_state['category_color'], str):
        with tab3.form('Category', clear_on_submit=True):
            c1, c2 = st.columns([2, 1])
            with c1:
                input_text(c1, st.session_state['category_color'])
                text_input = st.text_input(f"Nueva {st.session_state['nuevo'].lower()}",
                              placeholder=f"Nombre de nueva {st.session_state['nuevo'].lower()}",
                              label_visibility='collapsed',
                              key=f"new_{st.session_state['nuevo'].lower()}")
            with c2:
                button_submit(c2, st.session_state['category_color'])
                submitted = c2.form_submit_button('Guardar')

            if submitted:
                if st.session_state['nuevo']=='Categoría':
                    inserted = bonita_routine.insert_one({'category': text_input,
                                                          'color': st.session_state['category_color'],
                                                          'tasks': []
                                                          })
                    if inserted.acknowledged:
                        st.success(f'Nueva Categoría: **{text_input}** guardada.', icon="✅")
                        time.sleep(3)
                        st.session_state['add_cat_or_act'] = False
                        st.session_state['category_color'] = None
                        print('se logró en categoría')
                        st.rerun()
                    else:
                        st.error('''Error al guardar en bd.
                                 Reintentar o comunicarle a
                                 tu científico de datos favorito ;)
                                 '''.replace('\n', ' ').strip())

                elif st.session_state['nuevo']=='Actividad':
                    cat_id = ''
                    for cat in db.values():
                        if cat['category']==st.session_state['loaded_category']:
                            cat_id = cat['_id']
                    inserted_act = bonita_duties.insert_one({'category': st.session_state['loaded_category'],
                                                             'category_id': cat_id,
                                                             'name': text_input,
                                                             'completed': [False for _ in range(7)]
                                                             })
                    if inserted_act.acknowledged:
                        st.success(f'Nueva Actividad: **{text_input}** guardada.', icon="✅")
                        time.sleep(3)
                        st.session_state['add_cat_or_act'] = False
                        st.session_state['category_color'] = None
                        print('se logró en actividad')
                        st.rerun()
                    else:
                        st.error('''Error al guardar en bd.
                                 Reintentar o comunicarle a
                                 tu científico de datos favorito ;)
                                 '''.replace('\n', ' ').strip())

    ####################################
    #                                  #
    # CRUD de categorías y actividades #
    #                                  #
    ####################################

    #############
    # CATEGORÍA #
    #############

    def start_edit_cat(category_id, category_name):
        st.session_state[f"start_edit_cat_{category_name}"] = not st.session_state[f"start_edit_cat_{category_name}"]
        if st.session_state[f"start_edit_cat_{category_name}"]==True:
            st.session_state[f'ed_cat_i_{category_name}_{str(category_id)[-5:]}'] = ':x:'
        else:
            st.session_state[f'ed_cat_i_{category_name}_{str(category_id)[-5:]}'] = ':pencil:'

    def edit_category(category_id, category_name):
        edited_cat = bonita_routine.update_one({'_id': category_id},
                                               {'$set': {
                                                   'category': st.session_state[f"edited_cat_{category_name}"]
                                                   }
                                                })
        if edited_cat.acknowledged:
            st.session_state[f"start_edit_cat_{category_name}"] = False
            st.session_state[f'ed_cat_i_{category_name}_{str(category_id)[-5:]}'] = ':pencil:'

    def delete_category(category_id):
        deleted_cat = bonita_routine.delete_one({'_id': category_id})
        if deleted_cat.acknowledged:
            # pilar_2.success('Categoría eliminada correctamente.') # this do work
            print('Categoría eliminada correctamente.\n')


    #############
    # ACTIVIDAD #
    #############

    def handle_edit_act(act_id, act_name):
        st.session_state[f"start_edit_act_{act_name}"] = not st.session_state[f"start_edit_act_{act_name}"]
        if st.session_state[f"start_edit_act_{act_name}"]==True:
            st.session_state[f'ed_act_i_{act_name}_{str(act_id)[-5:]}'] = ':x:'
        else:
            st.session_state[f'ed_act_i_{act_name}_{str(act_id)[-5:]}'] = ':pencil:'

    def edit_activity(act_id, act_name):
        edited_act = bonita_duties.update_one({'_id': act_id},
                                              {'$set': {
                                                  'name': st.session_state[f"edited_act_{act_name}"]
                                                  }
                                               })
        if edited_act.acknowledged:
            st.session_state[f"start_edit_act_{act_name}"] = False
            st.session_state[f'ed_act_i_{act_name}_{str(act_id)[-5:]}'] = ':pencil:'

    def delete_activity(activity_id):
        deleted_act = bonita_duties.delete_one({'_id': activity_id})
        if deleted_act.acknowledged:
            # pilar_2.success('Actividad eliminada correctamente.') # this do work
            print('Actividad eliminada correctamente.\n')


    ###################################
    #                                 #
    # Visualización de catgs y actvds #
    #                                 #
    ###################################

    for catg in db.values():
        if f"start_edit_cat_{catg['category']}" not in st.session_state:
            st.session_state[f"start_edit_cat_{catg['category']}"] = False
        if f"ed_cat_i_{catg['category']}_{str(catg['_id'])[-5:]}" not in st.session_state:
            st.session_state[f"ed_cat_i_{catg['category']}_{str(catg['_id'])[-5:]}"] = ':pencil:'

        tupper = tab3.container(border=True)
        _, tc1, tc2, _, tc_3, _ = tupper.columns([1,1,3,1,2,1])

        tc1.color_picker(label=f"category_color_{catg['color']}",
                         key=f"cc_{catg['color']}_{catg['category'][-5:]}",
                         label_visibility='collapsed',
                         disabled=True,
                         value=catg['color'])

        if st.session_state[f"start_edit_cat_{catg['category']}"]==True:
            input_cat = tc2.chat_input('Editar categoría',
                                       key=f"edited_cat_{catg['category']}",
                                       on_submit=edit_category,
                                       args=(catg['_id'], catg['category']))
        else:
            tc2.write(catg['category'])

        button_edit_del_cat(tc_3)
        tc3_c1, tc3_c2 = tc_3.columns(2)
        tc3_c1.button(st.session_state[f"ed_cat_i_{catg['category']}_{str(catg['_id'])[-5:]}"],
                      key=f"edit_{catg['category']}",
                      help='Editar Categoría',
                      on_click=start_edit_cat,
                      args=(catg['_id'], catg['category']))
        tc3_c2.button(':wastebasket:',
                      key=f"del_{catg['category']}",
                      help='Eliminar Categoría',
                      on_click=delete_category,
                      args=(catg['_id'],))

        for act in catg['tasks']:
            if f"start_edit_act_{act['name']}" not in st.session_state:
                st.session_state[f"start_edit_act_{act['name']}"] = False
            if f"ed_act_i_{act['name']}_{str(act['id'])[-5:]}" not in st.session_state:
                st.session_state[f"ed_act_i_{act['name']}_{str(act['id'])[-5:]}"] = ':pencil:'

            sub_tupper = tupper.container(border=False)
            _, stc1, stc2, _ = sub_tupper.columns([3,4,3,2])

            if st.session_state[f"start_edit_act_{act['name']}"]==True:
                stc1.chat_input('Editar Actividad',
                                key=f"edited_act_{act['name']}",
                                on_submit=edit_activity,
                                args=([str(act['id']), act['name']]))
            else:
                stc1.write(act['name'])

            button_edit_del_act(stc2)
            sbt_c1, sbt_c2 = stc2.columns(2)
            sbt_c1.button(st.session_state[f"ed_act_i_{act['name']}_{str(act['id'])[-5:]}"],
                          key=f"edit_{catg['category']}_{act['name']}",
                          help='Editar Actividad',
                          on_click=handle_edit_act,
                          args=([act['id'], act['name']]))
            sbt_c2.button(':wastebasket:',
                          key=f"del_{catg['category']}_{act['name']}",
                          help='Eliminar Actividad',
                          on_click=delete_activity,
                          args=(act['id'],))
