from typing import List, Any, Dict
from collections import defaultdict
from operator import attrgetter
from dao import menu_repository
from flask import jsonify

from utils.log import logger


class RouterMen:
    def __init__(self):
        self.id: int = None
        self.parent_id: int = None
        self.path: str = None
        self.component: str = None
        self.name: str = None
        self.num: int = None
        self.hidden: bool = False
        self.meta: 'MenuMet' = MenuMet()
        self.children: List['RouterMen'] = []

    def set_id(self, id: int):
        self.id = id

    def set_parent_id(self, parent_id: int):
        self.parent_id = parent_id

    def set_path(self, path: str):
        self.path = path

    def set_component(self, component: str):
        self.component = component

    def set_name(self, name: str):
        self.name = name

    def set_num(self, num: int):
        self.num = num

    def set_hidden(self, hidden: bool):
        self.hidden = hidden

    def set_meta(self, meta: 'MenuMet'):
        self.meta = meta

    def to_dict(self):
        children_dicts = [child.to_dict() for child in self.children]
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "path": self.path,
            "component": self.component,
            "name": self.name,
            "num": self.num,
            "hidden": self.hidden,
            "meta": self.meta.to_dict(),
            "children": children_dicts,
        }

class MenuMet:
    def __init__(self):
        self.title: str = None
        self.icon: str = None
        self.isAffix: bool = False
        self.isFull: bool = False
        self.isHide: bool = False
        self.isKeepAlive: bool = True
        self.isLink: bool = None

    def set_title(self, title: str):
        self.title = title

    def set_icon(self, icon: str):
        self.icon = icon

    def set_isaffix(self, isAffix: bool):
        self.isAffix = isAffix

    def set_isFull(self, isFull: bool):
        self.isFull = isFull

    def set_isHide(self, isHide: bool):
        self.isHide = isHide

    def set_isKeepAlive(self, isKeepAlive: bool):
        self.isKeepAlive = isKeepAlive

    def set_isLink(self, isLink: bool):
        self.isLink = isLink

    def to_dict(self):
        return {
            "title": self.title,
            "icon": self.icon,
            "isAffix": self.isAffix,
            "isFull": self.isFull,
            "isHide": self.isHide,
            "isKeepAlive": self.isKeepAlive,
            "isLink": self.isLink,
        }

def transfer_menu_node(menus):
    menu_nodes = []
    try:
        for menu in menus:
            # print(menu)
            menu_node = dict()
            menu_node['id'] = menu['id']
            menu_node['icon'] = menu['icon']
            menu_node['parentId'] = menu['parentId']
            menu_node['name'] = menu['NAME']
            menu_node['url'] = menu['url']
            menu_node['levels'] = menu['levels']
            menu_node['isMenu'] = menu['ismenu']
            menu_node['num'] = menu['num']
            menu_node['code'] = menu['CODE']

            if menu['component'] is not None:
                menu_node['component'] = menu['component']

            if menu['hidden'] == "1":
                menu_node['hidden'] = True
            else:
                menu_node['hidden'] = False

            if menu['pcode'] is None:
                menu_node['pcode'] = ""
            else:
                menu_node['pcode'] = menu['pcode']
            menu_nodes.append(menu_node)
    except Exception as e:
        logger.error(e)

    return menu_nodes

def transfer_route_menu(menus: List[List[Any]]) -> List[RouterMen]:
    router_menus = []
    for i in range(len(menus)):
        source = menus[i]
        if source['component'] is None:
            continue

        menu = RouterMen()
        menu.set_path(str(source['url']))
        menu.set_name(str(source['CODE']))

        meta = MenuMet()
        meta.set_icon(str(source['icon']))
        meta.set_title(str(source['NAME']))
        menu.set_num(int(source['num']))
        menu.set_parent_id(int(source['parentId']))

        if source['component'] is not None:
            component = str(source['component'])
            if component.startswith("views/"):
                component = component[5:]
            menu.set_component(component)

        menu.set_id(int(source['id']))
        menu.set_meta(meta)

        if str(source['hidden']) == "1":
            meta.set_isHide(True)

        router_menus.append(menu.to_dict())

    # print(router_menus)
    # 使用 jsonify 返回 JSON 响应
    return router_menus

def generate_tree(list: List) -> List:
    result = []
    menu_map = {menu['id']: menu for menu in list}
    for menu_node in menu_map.values():
        menu_node['children'] = []
    for menu_node in menu_map.values():
        if menu_node['parentId'] != 0:
            parent_node = menu_map.get(menu_node['parentId'])
            parent_node['children'].append(menu_node)
        else:
            result.append(menu_node)
    return result

def generate_router_tree(list: List[RouterMen]) -> List[RouterMen]:
    result = []
    menu_map = {menu['id']: menu for menu in list}
    for menu_node in menu_map.values():
        if menu_node['parent_id'] != 0:
            parent_node = menu_map.get(menu_node['parent_id'])
            if parent_node is not None:
                parent_node['children'].append(menu_node)
        else:
            result.append(menu_node)
    # print(result)
    return result


def sort_router_tree(list: List[RouterMen]) -> None:
    list.sort(key=lambda item: item['num'])

def sort_tree(list: List) -> None:
    list.sort(key=lambda item: item['num'])

def get_menus():
    menu_list = transfer_menu_node(menu_repository.get_menus())
    result = generate_tree(menu_list)

    for menu_node in result:
        if menu_node['children']:
            sort_tree(menu_node['children'])
            for menu_node1 in menu_node['children']:
                if menu_node1['children']:
                    sort_tree(menu_node1['children'])

    sort_tree(result)

    return result

def get_side_bar_menus(role_ids: List[int]) -> List[RouterMen]:
    menu_list = transfer_route_menu(menu_repository.get_menus_by_roleIds(role_ids))
    result = generate_router_tree(menu_list)

    for menu_node in result:
        if menu_node['children']:
            sort_router_tree(menu_node['children'])
            for menu_node1 in menu_node['children']:
                if menu_node1['children']:
                    sort_router_tree(menu_node1['children'])

    sort_router_tree(result)

    return result



def get_button_auth(role_ids: List[int]) -> Dict[str, List[str]]:
    menu_list = menu_repository.query_menus_by_roleIds(role_ids)
    menu_map = {menu['code']: menu for menu in menu_list}
    result = []
    for menu in menu_list:
        if menu['ismenu'] == 0 :
            map_data = {'pcode': (menu_map[menu['pcode']])['code']}
            if map_data is not None:
                map_data['code'] = menu['code']
            result.append(map_data)

    group = defaultdict(list)
    for item in result:
        group[item['pcode']].append(item['code'])

    return dict(group)