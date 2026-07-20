"""店主后台路由.

登录使用邮箱或手机号身份、密码凭据和一次性验证码。
旧魔法链接路由仅兼容迁移前已经生成的链接。
"""
import hashlib
import copy
import mimetypes
import secrets
import time
import zipfile
import json
import smtplib
import urllib.request
from email.message import EmailMessage
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import (Blueprint, abort, current_app, flash, jsonify, redirect,
                   render_template, request, send_file, send_from_directory,
                   session, url_for)
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash

import re

import yaml as _yaml
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from .html_sanitizer import sanitize_richtext
from .tagging import generated_technical_tags

_LIVE_PREVIEW_CACHE = {}
_LIVE_PREVIEW_VERSION_CACHE = {}
_LIVE_PREVIEW_CACHE_TTL = 5
_LIVE_PREVIEW_VERSION_TTL = 1
_LIVE_PREVIEW_CACHE_MAX = 128


DETAIL_CONTENT_TYPE_TO_MODULE = {
    'text': 'detail_content_text',
    'image': 'detail_content_image',
    'video': 'detail_content_video',
    'media_text': 'detail_content_media_text',
    'gallery': 'detail_content_gallery',
    'table': 'detail_content_table',
    'heading': 'detail_content_heading',
    'note': 'detail_content_note',
    'embed': 'detail_content_embed',
}
DETAIL_CONTENT_MODULE_TO_TYPE = {module_type: content_type for content_type, module_type in DETAIL_CONTENT_TYPE_TO_MODULE.items()}


def _detail_content_component_blocks():
    """Return genuinely independent fixed-content components for detail templates."""
    common_content = [
        {'key': 'slot_id', 'label': '', 'type': 'hidden', 'group': '内容', 'default': ''},
        {'key': 'title', 'label': '区块标题', 'type': 'text', 'group': '内容', 'default': ''},
    ]
    common_rules = [
        {'key': 'empty_behavior', 'label': '内容为空时', 'type': 'select', 'group': '显示规则', 'default': 'hide_module', 'options': [
            {'value': 'hide_module', 'label': '隐藏组件'},
            {'value': 'show_placeholder', 'label': '显示空状态'},
        ]},
        {'key': 'section_bg', 'label': '背景色', 'type': 'color', 'group': '样式', 'default': ''},
        {'key': 'text_color', 'label': '文字颜色', 'type': 'color', 'group': '样式', 'default': ''},
    ]
    specifics = {
        'text': [
            {'key': 'text_align', 'label': '文字对齐', 'type': 'select', 'group': '显示规则', 'default': 'left', 'options': [
                {'value': 'left', 'label': '居左'}, {'value': 'center', 'label': '居中'}, {'value': 'right', 'label': '居右'},
            ]},
        ],
        'image': [
            {'key': 'image_ratio', 'label': '图片比例', 'type': 'select', 'group': '显示规则', 'default': 'auto', 'options': [
                {'value': 'auto', 'label': '原始比例'}, {'value': '1/1', 'label': '1:1'}, {'value': '4/3', 'label': '4:3'}, {'value': '16/9', 'label': '16:9'},
            ]},
            {'key': 'image_radius', 'label': '图片圆角', 'type': 'text', 'group': '样式', 'default': '0'},
        ],
        'video': [
            {'key': 'video_ratio', 'label': '视频比例', 'type': 'select', 'group': '显示规则', 'default': '16/9', 'options': [
                {'value': '16/9', 'label': '16:9'}, {'value': '4/3', 'label': '4:3'}, {'value': 'auto', 'label': '原始比例'},
            ]},
        ],
        'media_text': [
            {'key': 'layout', 'label': '图文布局', 'type': 'select', 'group': '显示规则', 'default': 'image_left', 'options': [
                {'value': 'image_left', 'label': '左图右文'}, {'value': 'image_right', 'label': '右图左文'},
            ]},
            {'key': 'image_ratio', 'label': '图片比例', 'type': 'select', 'group': '显示规则', 'default': 'auto', 'options': [
                {'value': 'auto', 'label': '原始比例'}, {'value': '1/1', 'label': '1:1'}, {'value': '4/3', 'label': '4:3'}, {'value': '16/9', 'label': '16:9'},
            ]},
            {'key': 'image_radius', 'label': '图片圆角', 'type': 'text', 'group': '样式', 'default': '0'},
        ],
        'gallery': [
            {'key': 'gallery_columns', 'label': '每行图片数', 'type': 'select', 'group': '显示规则', 'default': '3', 'options': [
                {'value': '2', 'label': '2 张'}, {'value': '3', 'label': '3 张'}, {'value': '4', 'label': '4 张'},
            ]},
            {'key': 'max_images', 'label': '最多显示', 'type': 'number', 'group': '显示规则', 'default': 6},
        ],
        'table': [
            {'key': 'table_style', 'label': '表格样式', 'type': 'select', 'group': '显示规则', 'default': 'bordered', 'options': [
                {'value': 'bordered', 'label': '边框表格'}, {'value': 'striped', 'label': '斑马纹'}, {'value': 'minimal', 'label': '简洁分隔线'},
            ]},
        ],
        'heading': [
            {'key': 'heading_level', 'label': '标题级别', 'type': 'select', 'group': '显示规则', 'default': 'h2', 'options': [
                {'value': 'h2', 'label': 'H2'}, {'value': 'h3', 'label': 'H3'}, {'value': 'h4', 'label': 'H4'},
            ]},
            {'key': 'text_align', 'label': '文字对齐', 'type': 'select', 'group': '显示规则', 'default': 'left', 'options': [
                {'value': 'left', 'label': '居左'}, {'value': 'center', 'label': '居中'}, {'value': 'right', 'label': '居右'},
            ]},
        ],
        'note': [
            {'key': 'note_style', 'label': '提示样式', 'type': 'select', 'group': '显示规则', 'default': 'info', 'options': [
                {'value': 'info', 'label': '信息'}, {'value': 'success', 'label': '成功'}, {'value': 'warning', 'label': '警告'}, {'value': 'danger', 'label': '危险'},
            ]},
        ],
        'embed': [
            {'key': 'iframe_height', 'label': '嵌入高度', 'type': 'text', 'group': '显示规则', 'default': '520px'},
        ],
    }
    display_names = {
        'text': '文本内容', 'image': '图片内容', 'video': '视频内容', 'media_text': '图文内容',
        'gallery': '多图内容', 'table': '表格内容', 'heading': '章节标题',
        'note': '提示信息', 'embed': '嵌入页面',
    }
    blocks = []
    for content_type, module_type in DETAIL_CONTENT_TYPE_TO_MODULE.items():
        blocks.append({
            'name': module_type,
            'display_name': display_names[content_type],
            'category': 'detail',
            'icon': '',
            'description': f'详情页中的独立{display_names[content_type]}位置。',
            'fields': copy.deepcopy(common_content + specifics[content_type] + common_rules),
            'variants': [{'key': content_type, 'label': display_names[content_type], 'data_preset': {}}],
            'is_data_attr': False,
            'schema': None,
        })
    return blocks

from . import datasets, style_registry
from . import menu as menu_lib
from .translator import (generate_seo_description, generate_seo_title,
                         is_configured as translation_configured,
                         translate_json)
from .builder import build_site, build_template_preview, render_site_page
from .db import db
from . import media_service
from .template_loader import scan_templates
# CSRF 豁免：静态站点公开 API 无法提供 CSRF token, 需要豁免
# csrf 是 app/__init__.py 模块级变量, 在 create_app() 调用时已初始化
from app import csrf
from .models import (AccountEntitlement, AccountIdentity, AiCreditAccount, AiCreditTransaction,
                     AuditLog, BillingOrder, BillingPlan,
                     ExternalIdentity, LoginToken, Organization,
                     OrganizationInvitation, OrganizationMember, OrganizationSite, PasswordCredential,
                     Site, SiteSlugAlias, Subscription, Template, TotpCredential, User,
                     UserSession, VerificationCode)
from .site_storage import (copy_seed_data, init_site_folder, lang_root,
                            list_media_files, list_yaml_files, read_yaml,
                            rename_media_file, delete_media_file,
                            find_media_references, is_media_package_token,
                            media_package_name_from_token, media_package_token,
                            write_yaml)

bp = Blueprint('core', __name__)

mimetypes.add_type('application/wasm', '.wasm')

DETAIL_TEMPLATE_COMPONENT_BLOCKS = [
    {
        'name': 'detail_media',
        'display_name': '图片/图集',
        'category': 'detail',
        'icon': '',
        'description': '显示当前数据项的封面图、细节图或两者组合。',
        'palette_hidden': True,
        'fields': [
            {'key': 'source', 'label': '图片来源', 'type': 'select', 'group': '内容', 'default': 'cover_and_gallery', 'options': [
                {'value': 'cover_and_gallery', 'label': '封面图 + 细节图'},
                {'value': 'gallery_only', 'label': '只显示细节图'},
                {'value': 'cover_only', 'label': '只显示封面图'},
            ]},
            {'key': 'layout', 'label': '布局', 'type': 'select', 'group': '显示规则', 'default': 'gallery_top', 'options': [
                {'value': 'gallery_top', 'label': '大图在上'},
                {'value': 'gallery_left', 'label': '左右分栏'},
            ]},
            {'key': 'max_images', 'label': '最多显示', 'type': 'number', 'group': '显示规则', 'default': 6},
            {'key': 'empty_behavior', 'label': '无图片时', 'type': 'select', 'group': '显示规则', 'default': 'hide_module', 'options': [
                {'value': 'hide_module', 'label': '隐藏组件'},
                {'value': 'show_placeholder', 'label': '显示占位'},
            ]},
            {'key': 'image_ratio', 'label': '图片比例', 'type': 'select', 'group': '样式', 'default': '4/3', 'options': [
                {'value': '4/3', 'label': '4:3'},
                {'value': '1/1', 'label': '1:1'},
                {'value': '16/9', 'label': '16:9'},
                {'value': 'auto', 'label': '原始比例'},
            ]},
            {'key': 'image_radius', 'label': '圆角', 'type': 'text', 'group': '样式', 'default': '8px'},
            {'key': 'section_bg', 'label': '背景色', 'type': 'color', 'group': '样式', 'default': ''},
        ],
        'variants': [
            {'key': 'gallery_top', 'label': '上图下文', 'data_preset': {'layout': 'gallery_top'}},
            {'key': 'gallery_left', 'label': '左图右文', 'data_preset': {'layout': 'gallery_left'}},
        ],
        'is_data_attr': False,
        'schema': None,
    },
    {
        'name': 'detail_text',
        'display_name': '字段文本',
        'category': 'detail',
        'icon': '',
        'description': '读取当前数据项的正文、简介或指定字段，渲染一个文本区块。',
        'palette_hidden': True,
        'fields': [
            {'key': 'title', 'label': '区块标题', 'type': 'text', 'group': '内容', 'default': ''},
            {'key': 'content_field', 'label': '读取内容', 'type': 'select', 'group': '内容', 'default': 'body', 'options': [
                {'value': 'body', 'label': '正文'},
                {'value': 'description', 'label': '描述'},
                {'value': 'summary', 'label': '摘要'},
                {'value': 'content', 'label': '内容'},
            ]},
            {'key': 'empty_behavior', 'label': '内容为空时', 'type': 'select', 'group': '显示规则', 'default': 'hide_module', 'options': [
                {'value': 'hide_module', 'label': '隐藏组件'},
                {'value': 'show_placeholder', 'label': '显示空状态'},
            ]},
            {'key': 'text_align', 'label': '文字排版', 'type': 'select', 'group': '样式', 'default': 'left', 'options': [
                {'value': 'left', 'label': '居左'},
                {'value': 'center', 'label': '居中'},
                {'value': 'right', 'label': '居右'},
            ]},
            {'key': 'section_bg', 'label': '背景色', 'type': 'color', 'group': '样式', 'default': ''},
            {'key': 'text_color', 'label': '正文颜色', 'type': 'color', 'group': '样式', 'default': ''},
        ],
        'variants': [
            {'key': 'plain', 'label': '普通正文', 'data_preset': {'text_align': 'left'}},
            {'key': 'centered', 'label': '居中正文', 'data_preset': {'text_align': 'center'}},
        ],
        'is_data_attr': False,
        'schema': None,
    },
    {
        'name': 'detail_content_blocks',
        'display_name': '自由正文',
        'category': 'detail',
        'icon': '',
        'description': '用于结构不固定的文章或案例；内容编辑时可以自由增删和排列多种内容块。',
        'fields': [
            {'key': 'title', 'label': '区块标题', 'type': 'text', 'group': '内容', 'default': ''},
            {'key': 'empty_behavior', 'label': '内容为空时', 'type': 'select', 'group': '显示规则', 'default': 'hide_module', 'options': [
                {'value': 'hide_module', 'label': '隐藏组件'},
                {'value': 'show_placeholder', 'label': '显示空状态'},
            ]},
            {'key': 'section_bg', 'label': '背景色', 'type': 'color', 'group': '样式', 'default': ''},
            {'key': 'text_color', 'label': '正文颜色', 'type': 'color', 'group': '样式', 'default': ''},
        ],
        'variants': [
            {'key': 'blocks', 'label': '内容块', 'data_preset': {}},
        ],
        'is_data_attr': False,
        'schema': None,
    },
    *_detail_content_component_blocks(),
    {
        'name': 'detail_content',
        'display_name': '正文独立组件',
        'category': 'detail',
        'icon': '',
        'description': '每添加一次就是一个独立正文位置；选择文本、图片、视频、图文、多图、表格、标题、提示或嵌入。',
        'palette_hidden': True,
        'fields': [
            {'key': 'slot_id', 'label': '', 'type': 'hidden', 'group': '内容', 'default': ''},
            {'key': 'content_type', 'label': '内容类型', 'type': 'select', 'group': '内容', 'default': 'text', 'options': [
                {'value': 'text', 'label': '文本'},
                {'value': 'image', 'label': '图片'},
                {'value': 'video', 'label': '视频'},
                {'value': 'media_text', 'label': '图文'},
                {'value': 'gallery', 'label': '多图'},
                {'value': 'table', 'label': '表格'},
                {'value': 'heading', 'label': '标题'},
                {'value': 'note', 'label': '提示'},
                {'value': 'embed', 'label': '嵌入'},
            ]},
            {'key': 'title', 'label': '区块标题', 'type': 'text', 'group': '内容', 'default': ''},
            {'key': 'text_align', 'label': '文字对齐', 'type': 'select', 'group': '显示规则', 'default': 'left', 'show_if': {'field': 'content_type', 'value': 'text,heading'}, 'options': [
                {'value': 'left', 'label': '居左'},
                {'value': 'center', 'label': '居中'},
                {'value': 'right', 'label': '居右'},
            ]},
            {'key': 'heading_level', 'label': '标题级别', 'type': 'select', 'group': '显示规则', 'default': 'h2', 'show_if': {'field': 'content_type', 'value': 'heading'}, 'options': [
                {'value': 'h2', 'label': 'H2'},
                {'value': 'h3', 'label': 'H3'},
                {'value': 'h4', 'label': 'H4'},
            ]},
            {'key': 'layout', 'label': '图文布局', 'type': 'select', 'group': '显示规则', 'default': 'image_left', 'show_if': {'field': 'content_type', 'value': 'media_text'}, 'options': [
                {'value': 'image_left', 'label': '左图右文'},
                {'value': 'image_right', 'label': '右图左文'},
            ]},
            {'key': 'image_ratio', 'label': '图片比例', 'type': 'select', 'group': '显示规则', 'default': 'auto', 'show_if': {'field': 'content_type', 'value': 'image,media_text'}, 'options': [
                {'value': 'auto', 'label': '原始比例'},
                {'value': '1/1', 'label': '1:1'},
                {'value': '4/3', 'label': '4:3'},
                {'value': '16/9', 'label': '16:9'},
            ]},
            {'key': 'image_radius', 'label': '图片圆角', 'type': 'text', 'group': '样式', 'default': '0', 'show_if': {'field': 'content_type', 'value': 'image,media_text'}},
            {'key': 'video_ratio', 'label': '视频比例', 'type': 'select', 'group': '显示规则', 'default': '16/9', 'show_if': {'field': 'content_type', 'value': 'video'}, 'options': [
                {'value': '16/9', 'label': '16:9'},
                {'value': '4/3', 'label': '4:3'},
                {'value': 'auto', 'label': '原始比例'},
            ]},
            {'key': 'gallery_columns', 'label': '每行图片数', 'type': 'select', 'group': '显示规则', 'default': '3', 'show_if': {'field': 'content_type', 'value': 'gallery'}, 'options': [
                {'value': '2', 'label': '2 张'},
                {'value': '3', 'label': '3 张'},
                {'value': '4', 'label': '4 张'},
            ]},
            {'key': 'max_images', 'label': '最多显示', 'type': 'number', 'group': '显示规则', 'default': 6, 'show_if': {'field': 'content_type', 'value': 'gallery'}},
            {'key': 'table_style', 'label': '表格样式', 'type': 'select', 'group': '显示规则', 'default': 'bordered', 'show_if': {'field': 'content_type', 'value': 'table'}, 'options': [
                {'value': 'bordered', 'label': '边框表格'},
                {'value': 'striped', 'label': '斑马纹'},
                {'value': 'minimal', 'label': '简洁分隔线'},
            ]},
            {'key': 'note_style', 'label': '提示样式', 'type': 'select', 'group': '显示规则', 'default': 'info', 'show_if': {'field': 'content_type', 'value': 'note'}, 'options': [
                {'value': 'info', 'label': '信息'},
                {'value': 'success', 'label': '成功'},
                {'value': 'warning', 'label': '警告'},
                {'value': 'danger', 'label': '危险'},
            ]},
            {'key': 'iframe_height', 'label': '嵌入高度', 'type': 'text', 'group': '显示规则', 'default': '520px', 'show_if': {'field': 'content_type', 'value': 'embed'}},
            {'key': 'empty_behavior', 'label': '内容为空时', 'type': 'select', 'group': '显示规则', 'default': 'hide_module', 'options': [
                {'value': 'hide_module', 'label': '隐藏组件'},
                {'value': 'show_placeholder', 'label': '显示空状态'},
            ]},
            {'key': 'section_bg', 'label': '背景色', 'type': 'color', 'group': '样式', 'default': ''},
            {'key': 'text_color', 'label': '正文颜色', 'type': 'color', 'group': '样式', 'default': ''},
        ],
        'variants': [
            {'key': 'text', 'label': '文本', 'data_preset': {'content_type': 'text'}},
            {'key': 'image', 'label': '图片', 'data_preset': {'content_type': 'image'}},
            {'key': 'video', 'label': '视频', 'data_preset': {'content_type': 'video'}},
            {'key': 'media_text', 'label': '图文', 'data_preset': {'content_type': 'media_text', 'layout': 'image_left'}},
            {'key': 'gallery', 'label': '多图', 'data_preset': {'content_type': 'gallery'}},
            {'key': 'table', 'label': '表格', 'data_preset': {'content_type': 'table'}},
            {'key': 'heading', 'label': '标题', 'data_preset': {'content_type': 'heading'}},
            {'key': 'note', 'label': '提示', 'data_preset': {'content_type': 'note'}},
            {'key': 'embed', 'label': '嵌入', 'data_preset': {'content_type': 'embed'}},
        ],
        'is_data_attr': False,
        'schema': None,
    },
    {
        'name': 'detail_specs',
        'display_name': '规格参数',
        'category': 'detail',
        'icon': '',
        'description': '读取当前数据项的 specs、parameters 或 attributes 字段，渲染紧凑的键值参数列表。',
        'fields': [
            {'key': 'title', 'label': '区块标题', 'type': 'text', 'group': '内容', 'default': ''},
            {'key': 'source_field', 'label': '参数来源', 'type': 'select', 'group': '内容', 'default': 'specs', 'options': [
                {'value': 'specs', 'label': '规格'},
                {'value': 'parameters', 'label': '参数'},
                {'value': 'attributes', 'label': '属性'},
            ]},
            {'key': 'max_rows', 'label': '最多行数', 'type': 'number', 'group': '显示规则', 'default': 10},
            {'key': 'columns', 'label': '每行列数', 'type': 'select', 'group': '显示规则', 'default': '1', 'options': [
                {'value': '1', 'label': '1 列'},
                {'value': '2', 'label': '2 列'},
                {'value': '3', 'label': '3 列'},
            ]},
            {'key': 'hide_empty_rows', 'label': '空行处理', 'type': 'select', 'group': '显示规则', 'default': 'true', 'options': [
                {'value': 'true', 'label': '隐藏空行'},
                {'value': 'false', 'label': '保留空行'},
            ]},
            {'key': 'border_color', 'label': '分隔线颜色', 'type': 'color', 'group': '样式', 'default': '#e5e7eb'},
            {'key': 'section_bg', 'label': '背景色', 'type': 'color', 'group': '样式', 'default': ''},
        ],
        'variants': [
            {'key': 'list', 'label': '参数列表', 'data_preset': {}},
        ],
        'is_data_attr': False,
        'schema': None,
    },
    {
        'name': 'detail_table',
        'display_name': '自定义表格',
        'category': 'detail',
        'icon': '',
        'description': '按模板配置行列，逐格填写文字，可选择单元格文字链接。',
        'palette_hidden': True,
        'fields': [
            {'key': 'title', 'label': '区块标题', 'type': 'text', 'group': '内容', 'default': ''},
            {'key': 'table_rows', 'label': '行数', 'type': 'number', 'group': '表格', 'default': 3},
            {'key': 'table_cols', 'label': '列数', 'type': 'number', 'group': '表格', 'default': 2},
            {'key': 'cell_links', 'label': '单元格链接', 'type': 'select', 'group': '表格', 'default': 'optional', 'options': [
                {'value': 'none', 'label': '不需要链接'},
                {'value': 'optional', 'label': '可填写链接'},
            ]},
            {'key': 'hide_empty_rows', 'label': '空行处理', 'type': 'select', 'group': '显示规则', 'default': 'true', 'options': [
                {'value': 'true', 'label': '隐藏空行'},
                {'value': 'false', 'label': '保留空行'},
            ]},
            {'key': 'border_color', 'label': '边框颜色', 'type': 'color', 'group': '样式', 'default': '#e5e7eb'},
            {'key': 'section_bg', 'label': '背景色', 'type': 'color', 'group': '样式', 'default': ''},
        ],
        'variants': [
            {'key': 'table', 'label': '表格', 'data_preset': {'table_rows': 3, 'table_cols': 2}},
        ],
        'is_data_attr': False,
        'schema': None,
    },
    {
        'name': 'detail_link',
        'display_name': '按钮/链接',
        'category': 'detail',
        'icon': '',
        'description': '读取当前数据项的链接字段，渲染下载、跳转或联系按钮；每个组件对应一条链接。',
        'fields': [
            {'key': 'title', 'label': '区块标题', 'type': 'text', 'group': '内容', 'default': ''},
            {'key': 'label', 'label': '按钮文字', 'type': 'text', 'group': '内容', 'default': '了解更多'},
            {'key': 'url_field', 'label': '链接来源', 'type': 'select', 'group': '内容', 'default': 'link_url', 'options': [
                {'value': 'link_url', 'label': '链接'},
                {'value': 'download_url', 'label': '下载'},
                {'value': 'button_url', 'label': '按钮'},
                {'value': 'url', 'label': '通用'},
            ]},
            {'key': 'style', 'label': '显示样式', 'type': 'select', 'group': '显示规则', 'default': 'button', 'options': [
                {'value': 'button', 'label': '按钮'},
                {'value': 'text_link', 'label': '文字链接'},
            ]},
            {'key': 'hide_when_empty', 'label': '链接为空时', 'type': 'select', 'group': '显示规则', 'default': 'true', 'options': [
                {'value': 'true', 'label': '隐藏组件'},
                {'value': 'false', 'label': '显示空状态'},
            ]},
            {'key': 'link_color', 'label': '链接颜色', 'type': 'color', 'group': '样式', 'default': ''},
            {'key': 'section_bg', 'label': '背景色', 'type': 'color', 'group': '样式', 'default': ''},
        ],
        'variants': [
            {'key': 'button', 'label': '按钮', 'data_preset': {'style': 'button'}},
            {'key': 'text_link', 'label': '文字链接', 'data_preset': {'style': 'text_link'}},
        ],
        'is_data_attr': False,
        'schema': None,
    },
    {
        'name': 'detail_features',
        'display_name': '卖点特性',
        'category': 'detail',
        'icon': '',
        'description': '逐条填写产品卖点，渲染为图标/标题/说明卡片。',
        'fields': [
            {'key': 'title', 'label': '区块标题', 'type': 'text', 'group': '内容', 'default': ''},
            {'key': 'columns', 'label': '每行个数', 'type': 'select', 'group': '显示规则', 'default': '3', 'options': [
                {'value': '2', 'label': '2 个'},
                {'value': '3', 'label': '3 个'},
                {'value': '4', 'label': '4 个'},
            ]},
            {'key': 'empty_behavior', 'label': '内容为空时', 'type': 'select', 'group': '显示规则', 'default': 'hide_module', 'options': [
                {'value': 'hide_module', 'label': '隐藏组件'},
                {'value': 'show_placeholder', 'label': '显示空状态'},
            ]},
            {'key': 'card_bg', 'label': '卡片背景色', 'type': 'color', 'group': '样式', 'default': ''},
            {'key': 'section_bg', 'label': '背景色', 'type': 'color', 'group': '样式', 'default': ''},
        ],
        'variants': [
            {'key': 'cards', 'label': '卡片', 'data_preset': {'columns': '3'}},
        ],
        'is_data_attr': False,
        'schema': None,
    },
    {
        'name': 'detail_files',
        'display_name': '资料下载',
        'category': 'detail',
        'icon': '',
        'description': '填写规格书、说明书、认证文件等下载资料。',
        'fields': [
            {'key': 'title', 'label': '区块标题', 'type': 'text', 'group': '内容', 'default': '资料下载'},
            {'key': 'empty_behavior', 'label': '内容为空时', 'type': 'select', 'group': '显示规则', 'default': 'hide_module', 'options': [
                {'value': 'hide_module', 'label': '隐藏组件'},
                {'value': 'show_placeholder', 'label': '显示空状态'},
            ]},
            {'key': 'link_color', 'label': '链接颜色', 'type': 'color', 'group': '样式', 'default': ''},
            {'key': 'section_bg', 'label': '背景色', 'type': 'color', 'group': '样式', 'default': ''},
        ],
        'variants': [
            {'key': 'list', 'label': '列表', 'data_preset': {}},
        ],
        'is_data_attr': False,
        'schema': None,
    },
    {
        'name': 'detail_faq',
        'display_name': 'FAQ 问答',
        'category': 'detail',
        'icon': '',
        'description': '填写产品常见问题，渲染为问答列表。',
        'fields': [
            {'key': 'title', 'label': '区块标题', 'type': 'text', 'group': '内容', 'default': '常见问题'},
            {'key': 'empty_behavior', 'label': '内容为空时', 'type': 'select', 'group': '显示规则', 'default': 'hide_module', 'options': [
                {'value': 'hide_module', 'label': '隐藏组件'},
                {'value': 'show_placeholder', 'label': '显示空状态'},
            ]},
            {'key': 'border_color', 'label': '分隔线颜色', 'type': 'color', 'group': '样式', 'default': '#e5e7eb'},
            {'key': 'section_bg', 'label': '背景色', 'type': 'color', 'group': '样式', 'default': ''},
        ],
        'variants': [
            {'key': 'list', 'label': '问答列表', 'data_preset': {}},
        ],
        'is_data_attr': False,
        'schema': None,
    },
    {
        'name': 'detail_related',
        'display_name': '相关推荐',
        'category': 'detail',
        'icon': '',
        'description': '按分类或标签自动推荐同数据集中的其他条目。',
        'fields': [
            {'key': 'title', 'label': '区块标题', 'type': 'text', 'group': '内容', 'default': '相关推荐'},
            {'key': 'match_by', 'label': '推荐依据', 'type': 'select', 'group': '内容', 'default': 'category', 'options': [
                {'value': 'category', 'label': '同分类'},
                {'value': 'tags', 'label': '同标签'},
                {'value': 'all', 'label': '全部产品'},
            ]},
            {'key': 'max_items', 'label': '最多显示', 'type': 'number', 'group': '显示规则', 'default': 8},
            {'key': 'columns', 'label': '每行个数', 'type': 'select', 'group': '显示规则', 'default': '4', 'options': [
                {'value': '2', 'label': '2 个'},
                {'value': '3', 'label': '3 个'},
                {'value': '4', 'label': '4 个'},
            ]},
            {'key': 'auto_scroll', 'label': '自动滚动', 'type': 'select', 'group': '显示规则', 'default': 'true', 'options': [
                {'value': 'true', 'label': '开启'},
                {'value': 'false', 'label': '关闭'},
            ]},
            {'key': 'scroll_interval', 'label': '滚动间隔秒', 'type': 'select', 'group': '显示规则', 'default': '4', 'options': [
                {'value': '2', 'label': '2 秒'},
                {'value': '3', 'label': '3 秒'},
                {'value': '4', 'label': '4 秒'},
                {'value': '5', 'label': '5 秒'},
                {'value': '8', 'label': '8 秒'},
            ]},
            {'key': 'click_scroll', 'label': '点击滚动', 'type': 'select', 'group': '显示规则', 'default': 'true', 'options': [
                {'value': 'true', 'label': '开启'},
                {'value': 'false', 'label': '关闭'},
            ]},
            {'key': 'show_dots', 'label': '显示圆点', 'type': 'select', 'group': '显示规则', 'default': 'true', 'options': [
                {'value': 'true', 'label': '显示'},
                {'value': 'false', 'label': '隐藏'},
            ]},
            {'key': 'section_bg', 'label': '背景色', 'type': 'color', 'group': '样式', 'default': ''},
        ],
        'variants': [
            {'key': 'grid', 'label': '卡片网格', 'data_preset': {'columns': '4'}},
        ],
        'is_data_attr': False,
        'schema': None,
    },
]


def _default_detail_modules():
    return [
        {
            'type': 'detail_media',
            'variant': 'gallery_top',
            'data': {
                'source': 'cover_and_gallery',
                'layout': 'gallery_top',
                'max_images': 6,
                'empty_behavior': 'hide_module',
                'image_ratio': '4/3',
                'image_radius': '8px',
            },
        },
        {
            'type': 'detail_specs',
            'variant': 'list',
            'data': {
                'title': '',
                'source_field': 'specs',
                'max_rows': 10,
                'columns': '1',
                'hide_empty_rows': 'true',
                'mobile_layout': 'stacked',
                'border_color': '#e5e7eb',
            },
        },
        {
            'type': 'detail_link',
            'variant': 'button',
            'data': {
                'title': '',
                'label': '了解更多',
                'url_field': 'link_url',
                'style': 'button',
                'hide_when_empty': 'true',
            },
        },
    ]


def _default_detail_template(dataset_key, label=None):
    title = (label or dataset_key or '条目').strip() or '条目'
    return {
        'id': 'default',
        'name': f'默认{title}详情',
        'is_default': True,
        'modules': _default_detail_modules(),
        'required_fields': ['title', 'slug'],
        'optional_fields': ['cover', 'summary', 'detail_images', 'specs', 'category', 'tags', 'link_url'],
        'seo': {
            'title': '{title} - {site_name}',
            'description': '{summary}',
            'image': 'cover',
        },
    }


def _blank_detail_template(dataset_key, name):
    title = (name or dataset_key or '详情模板').strip() or '详情模板'
    return {
        'id': '',
        'name': title,
        'is_default': False,
        'modules': [],
        'required_fields': ['title', 'slug'],
        'optional_fields': [],
        'seo': {
            'title': '{title} - {site_name}',
            'description': '{summary}',
            'image': 'cover',
        },
    }


def _is_legacy_default_detail_template(tpl):
    if not isinstance(tpl, dict):
        return False
    is_default = tpl.get('is_default') is True or str(tpl.get('is_default')).lower() == 'true'
    if not is_default and str(tpl.get('id') or '') != 'default':
        return False
    modules = tpl.get('modules')
    return isinstance(modules, list) and len(modules) == 1 and isinstance(modules[0], dict) and modules[0].get('type') == 'item_data'


def _detail_content_type_from_module(module):
    if not isinstance(module, dict):
        return None
    module_type = str(module.get('type') or '')
    if module_type in DETAIL_CONTENT_MODULE_TO_TYPE:
        return DETAIL_CONTENT_MODULE_TO_TYPE[module_type]
    if module_type == 'detail_content':
        data = module.get('data') if isinstance(module.get('data'), dict) else {}
        content_type = str(data.get('content_type') or module.get('variant') or 'text')
        return content_type if content_type in DETAIL_CONTENT_TYPE_TO_MODULE else 'text'
    return None


def _upgrade_legacy_detail_content_modules(templates):
    """Convert old polymorphic modules and remove settings owned by other types."""
    type_fields = {
        'text': {'text_align'},
        'image': {'image_ratio', 'image_radius'},
        'video': {'video_ratio'},
        'media_text': {'layout', 'image_ratio', 'image_radius'},
        'gallery': {'gallery_columns', 'max_images'},
        'table': {'table_style'},
        'heading': {'heading_level', 'text_align'},
        'note': {'note_style'},
        'embed': {'iframe_height'},
    }
    specialized_fields = set().union(*type_fields.values())
    changed = False
    for template in templates or []:
        modules = template.get('modules') if isinstance(template, dict) else None
        if not isinstance(modules, list):
            continue
        slot_number = 0
        for module in modules:
            content_type = _detail_content_type_from_module(module)
            if content_type is None:
                continue
            target_type = DETAIL_CONTENT_TYPE_TO_MODULE[content_type]
            if module.get('type') != target_type:
                module['type'] = target_type
                changed = True
            if module.get('variant') != content_type:
                module['variant'] = content_type
                changed = True
            data = module.get('data') if isinstance(module.get('data'), dict) else {}
            module['data'] = data
            if not str(data.get('slot_id') or '').strip():
                data['slot_id'] = f'legacy-content-slot-{slot_number}'
                changed = True
            if 'content_type' in data:
                data.pop('content_type', None)
                changed = True
            for key in specialized_fields - type_fields[content_type]:
                if key in data:
                    data.pop(key, None)
                    changed = True
            slot_number += 1
    return changed


def _remove_redundant_detail_intro_modules(templates):
    """Remove the retired title/summary module from persisted detail templates."""
    changed = False
    for template in templates or []:
        modules = template.get('modules') if isinstance(template, dict) else None
        if not isinstance(modules, list):
            continue
        filtered = [
            module for module in modules
            if not (isinstance(module, dict) and module.get('type') == 'detail_intro')
        ]
        if len(filtered) != len(modules):
            template['modules'] = filtered
            changed = True
    return changed


def _ensure_page_detail_templates(site_id, dataset_key, label=None, lang=None):
    """Ensure list page config has a default detail template without touching existing data."""
    page = read_yaml(site_id, f'pages/{dataset_key}.yaml', default={}, lang=lang) or {}
    changed = False
    if 'modules' not in page:
        page['modules'] = []
        changed = True
    templates = page.get('detail_templates')
    if not isinstance(templates, list) or not templates:
        page['detail_templates'] = [_default_detail_template(dataset_key, label)]
        changed = True
    else:
        has_default = any(
            isinstance(tpl, dict) and (tpl.get('is_default') is True or str(tpl.get('is_default')).lower() == 'true')
            for tpl in templates
        )
        if not has_default and isinstance(templates[0], dict):
            templates[0]['is_default'] = True
            changed = True
        for tpl in templates:
            if _is_legacy_default_detail_template(tpl):
                tpl['modules'] = _default_detail_modules()
                tpl['optional_fields'] = ['cover', 'summary', 'detail_images', 'specs', 'category', 'tags', 'link_url']
                changed = True
        if _upgrade_legacy_detail_content_modules(templates):
            changed = True
    if _remove_redundant_detail_intro_modules(page.get('detail_templates')):
        changed = True
    if changed:
        write_yaml(site_id, f'pages/{dataset_key}.yaml', page, lang=lang)
    return page


def _detail_templates_for_page(page, dataset_key, label=None):
    templates = (page or {}).get('detail_templates')
    if not isinstance(templates, list) or not templates:
        return [_default_detail_template(dataset_key, label)]
    _upgrade_legacy_detail_content_modules(templates)
    _remove_redundant_detail_intro_modules(templates)
    return [tpl for tpl in templates if isinstance(tpl, dict)] or [_default_detail_template(dataset_key, label)]


def _default_detail_template_id(page, dataset_key, label=None):
    templates = _detail_templates_for_page(page, dataset_key, label)
    for tpl in templates:
        if tpl.get('is_default') is True or str(tpl.get('is_default')).lower() == 'true':
            return tpl.get('id') or 'default'
    return templates[0].get('id') or 'default'


def _unique_detail_template_id(templates, name):
    existing = {str(tpl.get('id') or '') for tpl in templates if isinstance(tpl, dict)}
    base = re.sub(r'[^a-z0-9-]+', '-', (name or '').strip().lower())
    base = base.strip('-') or 'template'
    candidate = base
    index = 2
    while candidate in existing:
        candidate = f'{base}-{index}'
        index += 1
    return candidate


def _detail_template_field_requirements(template, item=None):
    """Infer which dataset fields should be shown for a detail template.

    The inference is intentionally conservative: core fields are always
    available, template module options add specialized sections, and existing
    item data keeps its section visible so old content is never hidden away
    without a trace.
    """
    req = {
        'slug': True,
        'title': True,
        'summary': True,
        'media': True,
        'category': True,
        'tags': True,
        'body': False,
        'detail_images': False,
        'specs': False,
        'detail_tables': False,
        'link': False,
        'detail_features': False,
        'detail_files': False,
        'detail_faqs': False,
        'detail_related': False,
        'detail_content_blocks': False,
        'detail_content_slots': [],
        'seo': False,
    }
    modules = template.get('modules') if isinstance(template, dict) else []
    if not isinstance(modules, list):
        modules = []
    for module in modules:
        if not isinstance(module, dict):
            continue
        m_type = module.get('type') or ''
        data = module.get('data') if isinstance(module.get('data'), dict) else {}
        if m_type in ('item_detail', 'image_carousel', 'detail_media'):
            req['detail_images'] = True
        if m_type in ('item_detail', 'detail_specs'):
            req['specs'] = True
        if m_type == 'detail_table':
            req['detail_tables'] = True
        if m_type in ('contact_info', 'contact_form', 'featured_picks', 'detail_link'):
            req['link'] = True
        if m_type == 'detail_related':
            req['detail_related'] = True
        if m_type == 'detail_content_blocks':
            req['detail_content_blocks'] = True
        content_type = _detail_content_type_from_module(module)
        if content_type is not None:
            req['detail_content_blocks'] = True
            req['detail_content_slots'].append({
                'slot_id': str(data.get('slot_id') or f'legacy-content-slot-{len(req["detail_content_slots"])}'),
                'type': content_type,
                'label': str(data.get('title') or ''),
                'layout': str(data.get('layout') or 'image_left'),
            })
        if m_type == 'detail_features':
            req['detail_features'] = True
        if m_type == 'detail_files':
            req['detail_files'] = True
        if m_type == 'detail_faq':
            req['detail_faqs'] = True
        if m_type in ('text_content', 'detail_text'):
            req['body'] = True
        for key, value in data.items():
            key_l = str(key).lower()
            value_enabled = str(value).strip().lower() not in ('false', '0', 'no', 'off', '')
            if key_l == 'show_detail_images':
                req['detail_images'] = value_enabled
                continue
            if key_l == 'show_specs':
                req['specs'] = value_enabled
                continue
            if key_l == 'show_link':
                req['link'] = value_enabled
                continue
            if value_enabled and ('image' in key_l or key_l in ('show_arrows', 'show_dots', 'auto_scroll', 'scroll_interval')):
                req['detail_images'] = True
            if value_enabled and ('spec' in key_l or key_l in ('table_rows', 'table_cols', 'table_columns')):
                if m_type == 'detail_table':
                    req['detail_tables'] = True
                else:
                    req['specs'] = True
            if value_enabled and ('link' in key_l or key_l.endswith('_url') or key_l in ('btn_text', 'btn_url', 'button_text')):
                req['link'] = True
            if key_l.startswith('seo_'):
                req['seo'] = True
            if value not in (None, '', [], {}):
                if key_l in req:
                    req[key_l] = True
    item = item if isinstance(item, dict) else {}
    if item.get('detail_images') or (isinstance(item.get('detail_gallery'), dict) and item.get('detail_gallery', {}).get('images')):
        req['detail_images'] = True
    if item.get('specs'):
        req['specs'] = True
    if item.get('link_url') or item.get('link_text') or item.get('button_url') or item.get('download_url'):
        req['link'] = True
    if item.get('detail_features') or item.get('features'):
        req['detail_features'] = True
    if item.get('detail_files') or item.get('downloads'):
        req['detail_files'] = True
    if item.get('detail_faqs') or item.get('faqs'):
        req['detail_faqs'] = True
    if item.get('detail_content_blocks') or item.get('content_blocks'):
        req['detail_content_blocks'] = True
    if item.get('seo_title') or item.get('seo_description') or item.get('seo_image'):
        req['seo'] = True
    return req


def _detail_template_requirements_map(templates, item=None):
    result = {}
    for tpl in templates or []:
        if not isinstance(tpl, dict):
            continue
        tpl_id = tpl.get('id')
        if tpl_id:
            result[str(tpl_id)] = _detail_template_field_requirements(tpl, item)
    return result


_DETAIL_CONTENT_TYPE_LABELS = {
    'text': '文本内容', 'image': '图片内容', 'video': '视频内容', 'media_text': '图文内容',
    'gallery': '多图内容', 'table': '表格内容', 'heading': '章节标题',
    'note': '提示信息', 'embed': '嵌入页面',
}


def _detail_content_editor_state(template, item):
    """Align stored content blocks with stable template slots without duplicating free content."""
    modules = template.get('modules') if isinstance(template, dict) else []
    modules = modules if isinstance(modules, list) else []
    raw_blocks = item.get('detail_content_blocks') or item.get('content_blocks') or []
    blocks = [copy.deepcopy(block) for block in raw_blocks if isinstance(block, dict)]
    used = set()
    editor_blocks = []
    free_enabled = any(
        isinstance(module, dict) and module.get('type') == 'detail_content_blocks'
        for module in modules
    )
    slot_number = 0
    for module in modules:
        content_type = _detail_content_type_from_module(module)
        if content_type is None:
            continue
        data = module.get('data') if isinstance(module.get('data'), dict) else {}
        slot_id = str(data.get('slot_id') or f'legacy-content-slot-{slot_number}')
        match_index = next(
            (idx for idx, block in enumerate(blocks)
             if idx not in used and str(block.get('slot_id') or '') == slot_id),
            None,
        )
        if match_index is None:
            match_index = next(
                (idx for idx, block in enumerate(blocks)
                 if idx not in used and not block.get('slot_id')
                 and str(block.get('type') or 'text') == content_type),
                None,
            )
        block = copy.deepcopy(blocks[match_index]) if match_index is not None else {}
        if match_index is not None:
            used.add(match_index)
        block['type'] = content_type
        block['slot_id'] = slot_id
        block['_template_slot'] = True
        block['_slot_label'] = str(data.get('title') or _DETAIL_CONTENT_TYPE_LABELS.get(content_type, content_type))
        if content_type == 'media_text' and not block.get('layout'):
            block['layout'] = data.get('layout') or 'image_left'
        if content_type == 'note':
            block['style'] = data.get('note_style') or block.get('style') or 'info'
        editor_blocks.append(block)
        slot_number += 1
    for idx, block in enumerate(blocks):
        if idx in used:
            continue
        block['_template_slot'] = False
        block['_orphaned_content'] = not free_enabled
        editor_blocks.append(block)
    return editor_blocks, free_enabled


def _detail_template_rule_value(template, key, default=None):
    modules = template.get('modules') if isinstance(template, dict) else []
    if not isinstance(modules, list):
        return default
    for module in modules:
        if not isinstance(module, dict) or module.get('type') != 'item_data':
            continue
        data = module.get('data') if isinstance(module.get('data'), dict) else {}
        if key in data and data.get(key) not in (None, ''):
            return data.get(key)
    return default


def _suggest_tags_from_fields(fields, limit=8):
    tags = []
    for source in (fields.get('title'), fields.get('category')):
        if isinstance(source, str):
            tags.extend([part.strip() for part in re.split(r'[,，\s/|]+', source) if part.strip()])
    specs = fields.get('specs')
    if isinstance(specs, list):
        for spec in specs:
            if not isinstance(spec, dict):
                continue
            for source in (spec.get('name'), spec.get('value')):
                if isinstance(source, str):
                    tags.extend([part.strip() for part in re.split(r'[,，\s/|]+', source) if part.strip()])
    seen = set()
    result = []
    for tag in tags:
        normalized = tag.lower()
        if len(tag) < 2 or normalized in seen:
            continue
        seen.add(normalized)
        result.append(tag)
        if len(result) >= limit:
            break
    return result


def _parse_tags_input(value):
    """Parse the admin tags input without breaking phrases that contain spaces."""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        raw_parts = value
    else:
        raw = str(value).strip()
        if not raw:
            return []
        raw_parts = re.split(r'[,，;；\n\r]+', raw)
    result = []
    seen = set()
    for part in raw_parts:
        tag = str(part or '').strip()
        if not tag or tag in seen:
            continue
        seen.add(tag)
        result.append(tag)
    return result


def _apply_detail_template_autofill(fields, template, page_label=None):
    if not isinstance(fields, dict):
        return fields
    auto_category = _detail_template_rule_value(template, 'auto_category', 'inherit')
    if auto_category == 'inherit' and 'category' not in fields and page_label:
        fields['category'] = page_label
    auto_tags = _detail_template_rule_value(template, 'auto_tags', 'suggest')
    if auto_tags == 'suggest':
        generated = generated_technical_tags(fields)
        if generated:
            # 新版标签由结构化参数确定；保存时同步刷新，不继续依赖旧手填值。
            fields['tags'] = generated
        elif 'tags' not in fields:
            suggested = _suggest_tags_from_fields(fields)
            if suggested:
                fields['tags'] = suggested
    return fields


def _ensure_detail_templates_for_menu(site_id, menu_items):
    for entry in menu_lib.collect_list_targets(menu_items):
        target = entry.get('target')
        if target:
            _ensure_page_detail_templates(site_id, target, entry.get('label'))


def _hex_to_rgb(hex_color):
    """将 #rrggbb 转为 (r, g, b) 整数元组；无效输入返回黑色 (0, 0, 0)."""
    h = hex_color.lstrip('#')
    if len(h) < 6:
        return (0, 0, 0)
    try:
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    except (ValueError, IndexError):
        return (0, 0, 0)


def _darken(hex_color, factor=0.1):
    """将 hex 颜色变暗 factor (0-1)."""
    r, g, b = _hex_to_rgb(hex_color)
    return '#{:02x}{:02x}{:02x}'.format(
        max(0, int(r * (1 - factor))),
        max(0, int(g * (1 - factor))),
        max(0, int(b * (1 - factor))),
    )


def _lighten(hex_color, factor=0.1):
    """将 hex 颜色变亮 factor (0-1)."""
    r, g, b = _hex_to_rgb(hex_color)
    return '#{:02x}{:02x}{:02x}'.format(
        min(255, int(r + (255 - r) * factor)),
        min(255, int(g + (255 - g) * factor)),
        min(255, int(b + (255 - b) * factor)),
    )
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'ogg', 'mov'}
ALLOWED_FILE_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_VIDEO_EXTENSIONS | {
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'csv', 'zip'
}
MAX_GENERIC_FILE_BYTES = 32 * 1024 * 1024
MAX_MEDIA_PACKAGE_BYTES = 64 * 1024 * 1024
MAX_MEDIA_PACKAGE_UNCOMPRESSED_BYTES = 96 * 1024 * 1024
MAX_MEDIA_PACKAGE_DEPTH = 10


AUTH_EXEMPT_ENDPOINTS = {
    'core.login',
    'core.register',
    'core.register_verify',
    'core.organization_invitation_accept',
    'core.password_setup',
    'core.password_setup_verify',
    'core.magic_login',
    # template_preview 只渲染模板自带的种子数据, 不涉及任何用户私有内容, 可免登录。
    'core.template_preview',
    # 注意: preview / preview_site / preview_or_build 吐的是店主 output 下的真实
    # 私有数据, 已从免登录名单移除, 改为在各路由内做 _require_site_access 归属校验。
    # site_asset 免登录：路由内部通过 session / Referer 自行定位资源目录，
    # 模板预览（无站点归属）也需要访问 seed_data/assets 下的资源。
    'core.site_asset',
    'core.media_package_index',
    'core.media_package_asset',
}


def _safe_send_from_directory(base_dir, relative_path):
    """加固版 send_from_directory: 解析 symlink 后强制校验目标仍在 base_dir 内,
    阻断符号链接逃逸 + 兜底防御 (Flask safe_join 自身也已经防 ../, 这里多一层保险).
    """
    base_real = Path(base_dir).resolve()
    full_real = (base_real / relative_path).resolve()
    try:
        full_real.relative_to(base_real)
    except ValueError:
        abort(403, '非法路径')
    return send_from_directory(base_real, relative_path)


def _hash_token(raw_token):
    """对魔法链接 token 做 SHA-256；数据库不保存明文 token."""
    return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()


def _normalize_email(email):
    return (email or '').strip().lower()


def _normalize_identity(value):
    """规范化邮箱或国际手机号，返回 (类型, 值)；非法输入返回 (None, None)。"""
    value = (value or '').strip()
    if '@' in value:
        email = value.lower()
        if re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
            return 'email', email
        return None, None
    phone = re.sub(r'[\s()-]', '', value)
    if phone.startswith('00'):
        phone = '+' + phone[2:]
    if re.fullmatch(r'\+?[1-9]\d{7,14}', phone):
        return 'phone', phone
    return None, None


def _valid_password(password):
    return (len(password or '') >= 8
            and bool(re.search(r'[A-Za-z]', password or ''))
            and bool(re.search(r'\d', password or '')))


def _identity_for_user(user):
    """优先返回主身份；旧账户在完成迁移前回退到原邮箱。"""
    identity = AccountIdentity.query.filter_by(user_id=user.id, is_primary=True).first()
    if not identity:
        identity = AccountIdentity.query.filter_by(user_id=user.id).order_by(AccountIdentity.id).first()
    return identity


def _public_identifier(user):
    identity = _identity_for_user(user)
    return identity.identifier if identity else user.email


def _account_avatar_path(user_id):
    return Path(current_app.config['UPLOADS_DIR']) / 'avatars' / f'{int(user_id)}.webp'


def _account_avatar_url(user):
    if not user:
        return ''
    path = _account_avatar_path(user.id)
    return (url_for('core.account_avatar', user_id=user.id, v=int(path.stat().st_mtime))
            if path.is_file() else '')


def _user_can_create_sites(user):
    """旧账户无资格记录时保持原有建站能力；受邀注册会显式写入 false。"""
    if not user:
        return False
    if user.role == 'admin':
        return True
    entitlement = AccountEntitlement.query.filter_by(user_id=user.id).first()
    return entitlement.can_create_sites if entitlement else True


def _pending_organization_invitation(token):
    """按一次性明文令牌读取有效邀请；数据库只保存 SHA-256。"""
    if not token:
        return None
    invitation = OrganizationInvitation.query.filter_by(
        token_hash=_hash_token(token), status='pending'
    ).first()
    if not invitation:
        return None
    expires_at = invitation.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= datetime.now(timezone.utc):
        invitation.status = 'expired'
        db.session.commit()
        return None
    return invitation


def _user_matches_invitation(user, invitation):
    return bool(AccountIdentity.query.filter_by(
        user_id=user.id, identifier=invitation.identifier
    ).filter(AccountIdentity.verified_at.isnot(None)).first())


def _accept_organization_invitation(invitation, user):
    """调用方负责提交；成员关系和邀请消费必须同事务完成。"""
    membership = OrganizationMember.query.filter_by(
        organization_id=invitation.organization_id, user_id=user.id
    ).first()
    if membership:
        membership.status = 'active'
        if membership.role != 'owner':
            membership.role = invitation.role
    else:
        db.session.add(OrganizationMember(
            organization_id=invitation.organization_id, user_id=user.id,
            role=invitation.role, status='active',
        ))
    invitation.status = 'accepted'
    invitation.accepted_by = user.id
    invitation.accepted_at = datetime.now(timezone.utc)


def _invitation_landing_url(invitation):
    site = db.session.query(Site).join(
        OrganizationSite, OrganizationSite.site_id == Site.id
    ).filter(
        OrganizationSite.organization_id == invitation.organization_id,
        Site.soft_deleted_at.is_(None),
    ).order_by(Site.updated_at.desc()).first()
    if site:
        return url_for('core.overview', site=site.id)
    return url_for('core.account', section='organization', org=invitation.organization_id)


def _complete_invitation_for_user(invitation, user):
    if not _user_matches_invitation(user, invitation):
        flash('当前登录账号与团队邀请的邮箱或手机号不一致', 'danger')
        return redirect(url_for('core.account', section='organization'))
    _accept_organization_invitation(invitation, user)
    _write_audit(user, 'organization.invitation.accept',
                 f'接受团队“{invitation.organization.name}”邀请',
                 organization_id=invitation.organization_id,
                 details={'role': invitation.role, 'invitation_id': invitation.id})
    db.session.commit()
    session.pop('pending_invitation_token', None)
    flash(f'已加入团队“{invitation.organization.name}”', 'success')
    return redirect(_invitation_landing_url(invitation))


def _start_user_session(user):
    """创建可撤销会话，Cookie session 中只保存随机令牌。"""
    raw_token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    login_session = UserSession(
        user_id=user.id,
        token_hash=_hash_token(raw_token),
        ip_address=(request.headers.get('X-Forwarded-For', request.remote_addr or '').split(',')[0].strip()[:45]),
        user_agent=(request.headers.get('User-Agent') or '')[:500],
        last_seen_at=now,
        expires_at=now + timedelta(days=30),
    )
    user.last_login_at = now
    db.session.add(login_session)
    db.session.commit()
    session.clear()
    session['user_id'] = user.id  # 兼容尚未迁移的内部代码。
    session['auth_session_token'] = raw_token


def _create_verification_code(identity_type, identifier, purpose, payload=None):
    """生成一次性验证码；开发环境可回显，生产环境必须接入真实发送器。"""
    display_code = (current_app.testing or current_app.debug
                    or current_app.config.get('VERIFICATION_CODE_MODE') == 'display')
    code = f'{secrets.randbelow(1_000_000):06d}'
    # 同一用途的新验证码会立即作废旧验证码，避免多个有效码并存。
    VerificationCode.query.filter_by(
        identifier=identifier, purpose=purpose, consumed_at=None
    ).update({'consumed_at': datetime.now(timezone.utc)})
    record = VerificationCode(
        identity_type=identity_type,
        identifier=identifier,
        purpose=purpose,
        code_hash=_hash_token(code),
        payload=payload or {},
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        ip_address=(request.headers.get('X-Forwarded-For', request.remote_addr or '').split(',')[0].strip()[:45]),
    )
    db.session.add(record)
    db.session.commit()
    if display_code:
        current_app.logger.info('Verification code purpose=%s identifier=%s code=%s', purpose, identifier, code)
        return code
    try:
        _deliver_verification_code(identity_type, identifier, purpose, code)
    except Exception as exc:
        # 发送失败的验证码绝不能留在数据库中继续有效。
        db.session.delete(record)
        db.session.commit()
        current_app.logger.exception('验证码发送失败: type=%s purpose=%s', identity_type, purpose)
        raise RuntimeError('验证码发送失败，请稍后重试或联系管理员') from exc
    return None


def _deliver_verification_code(identity_type, identifier, purpose, code):
    """通过标准 SMTP 或短信 Webhook 发送验证码，不绑定具体供应商。"""
    if identity_type == 'email':
        host = current_app.config.get('SMTP_HOST')
        sender = current_app.config.get('SMTP_FROM') or current_app.config.get('SMTP_USERNAME')
        if not host or not sender:
            raise RuntimeError('SMTP 未配置')
        message = EmailMessage()
        message['Subject'] = '网站工作台验证码'
        message['From'] = sender
        message['To'] = identifier
        message.set_content(f'你的验证码是 {code}，10 分钟内有效。用途：{purpose}。如非本人操作请忽略。')
        with smtplib.SMTP(host, current_app.config.get('SMTP_PORT', 587), timeout=10) as smtp:
            if current_app.config.get('SMTP_USE_TLS'):
                smtp.starttls()
            username = current_app.config.get('SMTP_USERNAME')
            if username:
                smtp.login(username, current_app.config.get('SMTP_PASSWORD', ''))
            smtp.send_message(message)
        return
    webhook = current_app.config.get('SMS_WEBHOOK_URL')
    if not webhook:
        raise RuntimeError('短信 Webhook 未配置')
    body = json.dumps({'phone': identifier, 'code': code, 'purpose': purpose}).encode('utf-8')
    headers = {'Content-Type': 'application/json'}
    token = current_app.config.get('SMS_WEBHOOK_TOKEN')
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(webhook, data=body, headers=headers, method='POST')
    with urllib.request.urlopen(req, timeout=10) as response:
        if response.status < 200 or response.status >= 300:
            raise RuntimeError(f'短信服务返回 {response.status}')


def _consume_verification_code(identifier, purpose, code):
    record = VerificationCode.query.filter_by(
        identifier=identifier, purpose=purpose, consumed_at=None
    ).order_by(VerificationCode.id.desc()).first()
    if not record or record.attempt_count >= 5:
        return None
    record.attempt_count += 1
    now = datetime.now(timezone.utc)
    expires = record.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < now or not secrets.compare_digest(record.code_hash, _hash_token((code or '').strip())):
        db.session.commit()
        return None
    record.consumed_at = now
    db.session.commit()
    return record


# 图片单边像素上限, 防御解码炸弹 (1KB PNG 解开成 1GB 那种)
MAX_IMAGE_PIXELS = 16_000_000  # 约 4000x4000
MAX_IMAGE_BYTES = 12 * 1024 * 1024  # 单图最大 12MB


def _check_upload_size(file_storage, max_bytes, label='文件'):
    """通过 stream.seek 获取真实字节数, 超限直接报错."""
    stream = file_storage.stream
    try:
        stream.seek(0, 2)
        size = stream.tell()
    finally:
        stream.seek(0)
    if size > max_bytes:
        raise ValueError(f'{label}过大: {size // 1024}KB > {max_bytes // 1024}KB 上限')
    return size


def _upload_convert_webp_enabled(file_storage):
    """Return whether this upload field should convert raster images to WebP."""
    field_name = getattr(file_storage, 'name', '') or ''
    candidates = []
    if field_name:
        candidates.append(f'{field_name}_convert_webp')
        if field_name.endswith('_file'):
            candidates.append(f'{field_name[:-5]}_convert_webp')
    candidates.append('convert_webp')
    for name in candidates:
        if name in request.form:
            values = request.form.getlist(name)
            return any(value == 'true' for value in values) if values else request.form.get(name) != 'false'
    return True


def _save_uploaded_image(site_id, file_storage, prefix='image', convert_webp=None):
    """保存上传图片到 sites/<id>/assets/uploads/，默认转换为 WebP，返回站点内绝对路径.

    返回示例: /assets/uploads/product-cover-20260509153000.webp
    """
    if not file_storage or not file_storage.filename:
        return ''

    original = secure_filename(file_storage.filename)
    suffix = original.rsplit('.', 1)[-1].lower() if '.' in original else ''
    if suffix not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError('仅支持 JPG、PNG、GIF、WebP、SVG 图片')

    uploads_dir = Path(current_app.config['SITES_DIR']) / str(site_id) / 'assets' / 'uploads'
    uploads_dir.mkdir(parents=True, exist_ok=True)

    safe_prefix = secure_filename(prefix or 'image') or 'image'
    ts = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    hex_part = secrets.token_hex(4)

    if convert_webp is None:
        convert_webp = _upload_convert_webp_enabled(file_storage)

    # SVG 和取消转换的图片都保留原格式直接写入。
    if suffix == 'svg' or not convert_webp:
        _check_upload_size(file_storage, MAX_IMAGE_BYTES, label='图片')
        filename = f"{safe_prefix}-{ts}-{hex_part}.{suffix}"
        output_path = uploads_dir / filename
        file_storage.save(str(output_path))
        return f'/assets/uploads/{filename}'

    _check_upload_size(file_storage, MAX_IMAGE_BYTES, label='图片')

    try:
        from PIL import Image, ImageSequence
    except ImportError as exc:
        raise RuntimeError('缺少 Pillow 依赖，请先安装 requirements.txt') from exc

    filename = f"{safe_prefix}-{ts}-{hex_part}.webp"
    output_path = uploads_dir / filename

    # #25: 用 with 确保 PIL 句柄及时释放(代码卫生)。损坏图会在此抛 PIL 异常,
    # 由各编辑路由捕获并提示, 不再 500。
    with Image.open(file_storage.stream) as image:
        # 分辨率上限校验, Pillow 默认对超大图触发 DecompressionBombWarning, 这里直接拒绝
        w, h = image.size
        if w * h > MAX_IMAGE_PIXELS:
            raise ValueError(f'图片分辨率过大: {w}x{h} 超过 {MAX_IMAGE_PIXELS} 像素上限')
        first_frame = next(ImageSequence.Iterator(image)).convert('RGBA')
    background = Image.new('RGBA', first_frame.size, (255, 255, 255, 0))
    background.alpha_composite(first_frame)
    background.save(output_path, 'WEBP', quality=86, method=6)
    return f'/assets/uploads/{filename}'


def _filename_alt(file_storage):
    if not file_storage or not getattr(file_storage, 'filename', ''):
        return ''
    stem = Path(secure_filename(file_storage.filename)).stem
    return re.sub(r'[-_]+', ' ', stem).strip()


def _context_alt(*contexts, fallback=''):
    for ctx in contexts:
        if not isinstance(ctx, dict):
            continue
        for key in ('title', 'name', 'label', 'short_name', 'heading'):
            val = ctx.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
    return str(fallback or '').strip()


def _image_alt_key(field_name):
    field = str(field_name or '').strip()
    if not field:
        return 'alt'
    if field in ('cover', 'photo', 'logo'):
        return f'{field}_alt'
    if field in ('image', 'media', 'url', 'src'):
        return 'alt'
    if field.endswith('_url'):
        return f'{field[:-4]}_alt'
    return f'{field}_alt'


def _form_alt_value(form, field_name, *contexts, upload=None, existing=None):
    keys = []
    field = str(field_name or '').strip()
    if field:
        keys.extend([f'{field}_alt', _image_alt_key(field)])
    keys.append('alt')
    for key in dict.fromkeys(keys):
        if key in form:
            val = form.get(key, '').strip()
            if val:
                return val
    if existing:
        return str(existing).strip()
    return _context_alt(*contexts, fallback=_filename_alt(upload))


def _save_uploaded_media(site_id, file_storage, prefix='media'):
    """保存图片或视频；图片转 WebP，视频原样保存到 assets/uploads。"""
    if not file_storage or not file_storage.filename:
        return ''
    original = secure_filename(file_storage.filename)
    if not original:
        return ''
    suffix = original.rsplit('.', 1)[-1].lower() if '.' in original else ''
    if suffix in ALLOWED_IMAGE_EXTENSIONS:
        try:
            return _save_uploaded_image(site_id, file_storage, prefix=prefix)
        except Exception as exc:
            current_app.logger.warning('图片保存失败: %s', exc)
            return ''
    if suffix not in ALLOWED_VIDEO_EXTENSIONS:
        current_app.logger.warning('不支持的文件类型: %s', suffix)
        return ''

    # 视频体积上限 12MB; 更大体积请走 CDN 直传
    try:
        _check_upload_size(file_storage, MAX_IMAGE_BYTES, label='视频')
    except ValueError as exc:
        current_app.logger.warning('视频上传被拒: %s', exc)
        return ''

    uploads_dir = Path(current_app.config['SITES_DIR']) / str(site_id) / 'assets' / 'uploads'
    uploads_dir.mkdir(parents=True, exist_ok=True)
    safe_prefix = secure_filename(prefix or 'media') or 'media'
    filename = f"{safe_prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4)}.{suffix}"
    output_path = uploads_dir / filename
    file_storage.save(output_path)
    return f'/assets/uploads/{filename}'


def _save_any_file(site_id, file_storage, prefix='file'):
    """保存普通文件到 assets/uploads，图片/视频之外的文档等走这里。"""
    if not file_storage or not file_storage.filename:
        return ''
    original = secure_filename(file_storage.filename)
    if not original:
        raise ValueError('文件名无效')
    suffix = original.rsplit('.', 1)[-1].lower() if '.' in original else ''
    if suffix not in ALLOWED_FILE_EXTENSIONS or suffix in ALLOWED_IMAGE_EXTENSIONS or suffix in ALLOWED_VIDEO_EXTENSIONS:
        raise ValueError('不支持的文件类型')
    _check_upload_size(file_storage, MAX_GENERIC_FILE_BYTES, label='文件')

    uploads_dir = Path(current_app.config['SITES_DIR']) / str(site_id) / 'assets' / 'uploads'
    uploads_dir.mkdir(parents=True, exist_ok=True)
    safe_prefix = secure_filename(prefix or 'file') or 'file'
    stem = Path(original).stem
    safe_stem = secure_filename(stem) or safe_prefix
    filename = f"{safe_prefix}-{safe_stem}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4)}.{suffix}"
    output_path = uploads_dir / filename
    file_storage.save(output_path)
    return f'/assets/uploads/{filename}'


def _safe_zip_member_name(name):
    name = (name or '').replace('\\', '/').strip('/')
    if not name or name.startswith('.') or '\x00' in name:
        raise ValueError('网页包中包含非法文件名')
    path = Path(name)
    if path.is_absolute() or any(part in ('', '.', '..') or part.startswith('.') for part in path.parts):
        raise ValueError('网页包中包含非法路径')
    if len(path.parts) > MAX_MEDIA_PACKAGE_DEPTH:
        raise ValueError('网页包目录层级过深')
    return name


def _zip_strip_root(member_names):
    first_parts = [Path(name).parts for name in member_names]
    if not first_parts:
        return ''
    first = first_parts[0][0]
    if all(len(parts) > 1 and parts[0] == first for parts in first_parts):
        return first
    return ''


def _save_media_package(site_id, file_storage):
    """保存并解压网页包 zip，返回 {name, url, entry_url, category}。"""
    if not file_storage or not file_storage.filename:
        raise ValueError('请选择网页包 zip 文件')
    original = secure_filename(file_storage.filename)
    suffix = original.rsplit('.', 1)[-1].lower() if '.' in original else ''
    if suffix != 'zip':
        raise ValueError('网页包必须是 zip 文件')
    _check_upload_size(file_storage, MAX_MEDIA_PACKAGE_BYTES, label='网页包')

    try:
        archive = zipfile.ZipFile(file_storage.stream)
    except zipfile.BadZipFile as exc:
        raise ValueError('zip 文件无法读取') from exc

    with archive:
        infos = [info for info in archive.infolist() if not info.is_dir()]
        if not infos:
            raise ValueError('网页包不能为空')
        total_size = 0
        names = []
        for info in infos:
            total_size += info.file_size
            if total_size > MAX_MEDIA_PACKAGE_UNCOMPRESSED_BYTES:
                raise ValueError('网页包解压后体积过大')
            names.append(_safe_zip_member_name(info.filename))

        strip_root = _zip_strip_root(names)
        normalized = []
        for name in names:
            parts = Path(name).parts
            if strip_root:
                parts = parts[1:]
            if not parts:
                continue
            normalized.append('/'.join(parts))
        if 'index.html' not in {name.lower() for name in normalized}:
            raise ValueError('网页包根目录必须包含 index.html')

        package_root = Path(current_app.config['SITES_DIR']) / str(site_id) / 'assets' / 'media-packages'
        package_root.mkdir(parents=True, exist_ok=True)
        safe_stem = secure_filename(Path(original).stem) or 'media-package'
        package_name = f"{safe_stem}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4)}"
        target_dir = package_root / package_name
        target_dir.mkdir(parents=True, exist_ok=False)

        try:
            for info, name in zip(infos, names):
                parts = Path(name).parts
                if strip_root:
                    parts = parts[1:]
                if not parts:
                    continue
                rel = Path(*parts)
                target = (target_dir / rel).resolve()
                try:
                    target.relative_to(target_dir.resolve())
                except ValueError as exc:
                    raise ValueError('网页包中包含非法路径') from exc
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as src, target.open('wb') as dst:
                    dst.write(src.read())
        except Exception:
            if target_dir.exists():
                import shutil
                shutil.rmtree(target_dir, ignore_errors=True)
            raise

    entry_url = f'/media-packages/{package_name}/'
    return {
        'name': package_name,
        'display_name': package_name,
        'api_name': media_package_token(package_name),
        'url': entry_url,
        'entry_url': entry_url,
        'category': 'package',
        'category_label': '网页包',
        'is_package': True,
    }


# Media helpers live in media_service; keep these private names for the existing
# routes and form parser while we split routes.py incrementally.
ALLOWED_IMAGE_EXTENSIONS = media_service.ALLOWED_IMAGE_EXTENSIONS
ALLOWED_VIDEO_EXTENSIONS = media_service.ALLOWED_VIDEO_EXTENSIONS
_save_uploaded_image = media_service.save_uploaded_image
_filename_alt = media_service.filename_alt
_context_alt = media_service.context_alt
_image_alt_key = media_service.image_alt_key
_form_alt_value = media_service.form_alt_value
_save_uploaded_media = media_service.save_uploaded_media
_save_any_file = media_service.save_any_file
_safe_zip_member_name = media_service.safe_zip_member_name
_zip_strip_root = media_service.zip_strip_root
_save_media_package = media_service.save_media_package


def _uploaded_image_or_form(site_id, form_field, file_field=None, prefix='image'):
    """若上传了图片则返回 WebP URL，否则返回文本框中的原 URL。"""
    upload = request.files.get(file_field or f'{form_field}_file')
    if upload and upload.filename:
        # #25: 损坏图/超大图/不支持格式会抛异常, 这里捕获并提示, 回退到表单 URL,
        # 避免 product/post 编辑路径整个 500。
        try:
            return _save_uploaded_image(site_id, upload, prefix=prefix)
        except Exception as exc:
            current_app.logger.warning('图片上传保存失败(%s): %s', form_field, exc)
            flash(f'图片上传失败：{exc}', 'error')
    return request.form.get(form_field, '').strip()


def _field_looks_like_image(field):
    """匹配媒体字段（图片+视频+音频+嵌入），供 _parse_modules_form 处理上传文件。"""
    name = (field or '').lower()
    if name.startswith(('show_', 'hide_', 'max_', 'min_')):
        return False
    if name.endswith(('_alt', '_type', '_ratio', '_radius', '_position', '_size', '_width', '_height',
                      '_columns', '_count', '_color', '_opacity', '_align', '_layout', '_fit',
                      '_convert_webp')):
        return False
    return any(part in name for part in ('image', 'cover', 'background', 'media', 'photo', 'logo', 'video', 'audio', 'embed'))


def _current_user():
    """从 session 读取当前用户；无效 session 自动清理."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    user = User.query.get(user_id)
    if not user or user.status != 'active':
        session.pop('user_id', None)
        return None
    raw_token = session.get('auth_session_token')
    if raw_token:
        login_session = UserSession.query.filter_by(token_hash=_hash_token(raw_token), user_id=user.id).first()
        if not login_session or login_session.revoked_at:
            session.clear()
            return None
        expires = login_session.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires < datetime.now(timezone.utc):
            session.clear()
            return None
        # 限制写频率，避免每个静态资源请求都更新数据库。
        last_seen = login_session.last_seen_at
        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) - last_seen > timedelta(minutes=5):
            login_session.last_seen_at = datetime.now(timezone.utc)
            db.session.commit()
    return user


def _organization_role_for_site(user, site):
    """返回用户在关联站点上的最高组织角色；站点所有者不走此分支。"""
    roles = db.session.query(OrganizationMember.role).join(
        OrganizationSite, OrganizationSite.organization_id == OrganizationMember.organization_id
    ).filter(
        OrganizationMember.user_id == user.id,
        OrganizationMember.status == 'active',
        OrganizationSite.site_id == site.id,
    ).all()
    order = {'viewer': 1, 'editor': 2, 'admin': 3, 'owner': 4}
    return max((row[0] for row in roles), key=lambda value: order.get(value, 0), default=None)


def _user_can_access_site(user, site, write=False):
    if user.role == 'admin' or site.owner_id == user.id:
        return True
    role = _organization_role_for_site(user, site)
    return bool(role) and (not write or role in {'owner', 'admin', 'editor'})


def _require_site_access(site):
    """校验当前登录用户有权访问该 site（本人站点或平台 admin）。

    预览路由会吐出店主 output 下的真实 HTML/资源, 必须做归属校验,
    否则任何登录用户自增 site_id 就能读他人未发布的私密站点(跨用户 IDOR)。

    测试阶段可通过 PREVIEW_REQUIRE_LOGIN 环境变量控制：默认免登录（不校验），
    开发完成后设 PREVIEW_REQUIRE_LOGIN=1 恢复完整鉴权。
    """
    # 测试阶段预览免登录：跳过站点归属校验，方便分享预览链接
    if not current_app.config.get('PREVIEW_REQUIRE_LOGIN'):
        return None
    user = _current_user()
    if not user:
        abort(401)
    if not _user_can_access_site(user, site, write=request.method not in {'GET', 'HEAD', 'OPTIONS'}):
        abort(403)
    return user


def _site_from_ref(site_ref, include_deleted=False):
    """Resolve a public site slug, with numeric database IDs kept as legacy input."""
    raw = str(site_ref or '').strip().lower()
    if not raw:
        return None
    query = Site.query
    if not include_deleted:
        query = query.filter(Site.soft_deleted_at.is_(None))
    site = query.filter_by(slug=raw).first()
    if site is None:
        alias = SiteSlugAlias.query.filter_by(slug=raw).first()
        site = alias.site if alias and (include_deleted or alias.site.soft_deleted_at is None) else None
    if site is None and raw.isdigit():
        site = query.filter_by(id=int(raw)).first()
    return site


@bp.before_request
def require_login():
    """保护后台页面：除登录和静态预览外都需要登录.

    测试阶段预览页（/preview/ /preview_site/ /preview_or_build/）默认免登录，
    开发完成后在 .env 设 PREVIEW_REQUIRE_LOGIN=1 恢复登录要求。
    """
    if request.endpoint in AUTH_EXEMPT_ENDPOINTS:
        return None
    if request.endpoint and request.endpoint.startswith('static'):
        return None
    # 预览端点按配置决定是否免登录（测试阶段免登录，方便分享预览链接给同事看）
    PREVIEW_ENDPOINTS = {'core.preview', 'core.preview_site', 'core.preview_or_build'}
    if request.endpoint in PREVIEW_ENDPOINTS and not current_app.config.get('PREVIEW_REQUIRE_LOGIN'):
        return None
    user = _current_user()
    if not user:
        return redirect(url_for('core.login', next=request.full_path if request.query_string else request.path))
    # Legacy admin links used ?site=<numeric id>. Canonicalize them to the public slug.
    raw_site = request.args.get('site', '').strip()
    if request.method == 'GET' and raw_site.isdigit():
        legacy_site = Site.query.filter_by(id=int(raw_site)).filter(Site.soft_deleted_at.is_(None)).first()
        if legacy_site and _user_can_access_site(user, legacy_site):
            from urllib.parse import urlencode
            args = request.args.to_dict(flat=False)
            args['site'] = [legacy_site.slug]
            return redirect(f'{request.path}?{urlencode(args, doseq=True)}', code=302)
    return None


@bp.context_processor
def inject_context():
    """给所有模板注入站点上下文."""
    user = _current_user()
    site_ref = request.args.get('site', '').strip()
    site = None
    if site_ref:
        site = _site_from_ref(site_ref)
        if site and user and not _user_can_access_site(user, site):
            site = None
    elif user:
        # 与 _current_context 使用相同的解析顺序。共享站点成员首次登录时
        # 也必须在模板上下文中拿到站点，否则左侧菜单只会剩 ensure_home 补出的首页。
        cached_site_id = session.get('current_site_id')
        if cached_site_id is not None:
            site = Site.query.filter_by(id=int(cached_site_id)).filter(
                Site.soft_deleted_at.is_(None)
            ).first()
            if site and not _user_can_access_site(user, site):
                site = None
        if not site:
            query = Site.query.filter(Site.soft_deleted_at.is_(None))
            if user.role != 'admin':
                shared_ids = db.session.query(OrganizationSite.site_id).join(
                    OrganizationMember, OrganizationMember.organization_id == OrganizationSite.organization_id
                ).filter(OrganizationMember.user_id == user.id, OrganizationMember.status == 'active')
                query = query.filter(or_(Site.owner_id == user.id, Site.id.in_(shared_ids)))
            site = query.order_by(Site.id.desc()).first()
    site_id = site.id if site else None

    ctx = {
        'counts': {},
        'left_menu_items': [],
        'template_meta': {},
        'available_sites': [],
        'admin_languages': [],
        'current_lang': '',
        'current_language_label': '',
        'account_identifier': _public_identifier(user) if user else '',
        'account_avatar_url': _account_avatar_url(user),
        'can_create_sites': _user_can_create_sites(user) if user else False,
        'site_can_edit': False,
        'site_access_role': '',
    }

    if user:
        query = Site.query.filter(Site.soft_deleted_at.is_(None))
        if user.role != 'admin':
            shared_ids = db.session.query(OrganizationSite.site_id).join(
                OrganizationMember, OrganizationMember.organization_id == OrganizationSite.organization_id
            ).filter(OrganizationMember.user_id == user.id, OrganizationMember.status == 'active')
            query = query.filter(or_(Site.owner_id == user.id, Site.id.in_(shared_ids)))
        ctx['available_sites'] = query.order_by(Site.id.desc()).all()

    if site and site_id:
        site_role = ('platform_admin' if user and user.role == 'admin'
                     else 'owner' if user and site.owner_id == user.id
                     else _organization_role_for_site(user, site) if user else None)
        ctx['site_access_role'] = site_role or ''
        ctx['site_can_edit'] = bool(site_role in {'platform_admin', 'owner', 'admin', 'editor'})
        ctx['counts']['products'] = len(datasets.load(site_id, 'products') or [])
        ctx['counts']['posts'] = len(datasets.load(site_id, 'posts') or [])
        ctx['counts']['features'] = len(datasets.load(site_id, 'features') or [])

        # 左栏动态菜单：从 settings.yaml 读取 menu 列表
        settings = read_yaml(site_id, 'settings.yaml') or {}
        meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
        if meta_path.exists():
            ctx['template_meta'] = _yaml.safe_load(meta_path.read_text(encoding='utf-8')) or {}

        # 后台顶部语言选择器：优先显示站点已启用语言，异常数据回退到主题语言/站点默认语言。
        template_languages = ctx['template_meta'].get('languages') or []
        enabled_codes = site.enabled_languages or [l.get('code') for l in template_languages if l.get('code')]
        admin_languages = [l for l in template_languages if l.get('code') in enabled_codes]
        if not admin_languages:
            admin_languages = template_languages
        default_lang = (
            ctx['template_meta'].get('default_language')
            or site.default_language
            or (admin_languages[0].get('code') if admin_languages else 'zh-CN')
        )
        current_lang = request.args.get('lang', '').strip() or default_lang
        valid_codes = {l.get('code') for l in admin_languages}
        if valid_codes and current_lang not in valid_codes:
            current_lang = default_lang if default_lang in valid_codes else admin_languages[0].get('code')
        if not admin_languages and current_lang:
            admin_languages = [{'code': current_lang, 'name': current_lang}]
        current_lang_opt = next((l for l in admin_languages if l.get('code') == current_lang), None)
        current_label = (current_lang_opt or {}).get('name') or current_lang or '默认语言'
        ctx['admin_languages'] = admin_languages
        ctx['current_lang'] = current_lang
        ctx['current_language_label'] = f"{current_label} ({current_lang})" if current_lang else current_label

        raw_menu = settings.get('menu') or ctx['template_meta'].get('default_menu', [])
        # 强制裁剪深度, 防御恶意 yaml 通过深嵌套触发递归栈溢出
        raw_menu = menu_lib.cap_menu_depth(raw_menu)
        datasets_meta = ctx['template_meta'].get('datasets', [])
        normalized = menu_lib.ensure_home(
            menu_lib.normalize_for_render(
                menu_lib.upgrade_old_format(raw_menu, datasets_meta)
            )
        )
        ctx['left_menu_items'] = normalized

        # 收集所有层级中 type=list 的菜单项（供数据网格模块选择数据源）
        ctx['all_list_datasets'] = menu_lib.collect_list_targets(normalized)  # #22

    ctx['platform_domain'] = current_app.config.get('PLATFORM_DOMAIN', '') or 'mycompany.website'

    # 后台 UI 主色固定，不跟随网站前台主题色。
    theme_color = '#0d9488'
    ctx['admin_primary'] = theme_color
    ctx['admin_primary_rgb'] = ', '.join(str(v) for v in _hex_to_rgb(theme_color))
    ctx['admin_primary_hover'] = _darken(theme_color, 0.12)
    ctx['admin_primary_active'] = _darken(theme_color, 0.20)
    ctx['admin_primary_light'] = _lighten(theme_color, 0.85)
    ctx['admin_auto_save'] = bool((settings.get('admin') or {}).get('auto_save')) if site and site_id else False

    return ctx


def _current_context():
    """取当前登录用户和站点；普通用户只能访问自己的站点，admin 可访问全部.

    URL 中带 ?site=slug 时存入 session，后续资源请求（如 /assets/uploads/...）
    不带 ?site= 也能从 session 中取到正确的站点.
    """
    user = _current_user()
    if not user:
        abort(401)
    site_ref = request.args.get('site', '').strip()
    if site_ref:
        site = _site_from_ref(site_ref)
        if site:
            session['current_site_id'] = site.id  # session 和存储层继续使用稳定的内部 ID
    else:
        # 从 session 中取缓存的站点 ID，确保资源请求也能找到正确的站点
        site_id = session.get('current_site_id')
        if site_id is not None:
            site = Site.query.filter_by(id=int(site_id)).filter(Site.soft_deleted_at.is_(None)).first()
        else:
            site = None
        if not site:
            query = Site.query.filter(Site.soft_deleted_at.is_(None))
            if user.role != 'admin':
                shared_ids = db.session.query(OrganizationSite.site_id).join(
                    OrganizationMember, OrganizationMember.organization_id == OrganizationSite.organization_id
                ).filter(OrganizationMember.user_id == user.id, OrganizationMember.status == 'active')
                query = query.filter(or_(Site.owner_id == user.id, Site.id.in_(shared_ids)))
            site = query.order_by(Site.id.desc()).first()
    if not site:
        abort(404, "尚无站点，请先从模板库创建站点")
    if not _user_can_access_site(user, site):
        abort(403, "无权访问该站点")
    if request.method not in {'GET', 'HEAD', 'OPTIONS'} and not _user_can_access_site(user, site, write=True):
        abort(403, "当前账号为只读权限，无法修改站点内容")
    return user, site


def _safe_next_url(candidate):
    """只允许跳回本站相对路径; 外站 URL / 协议跳转 / 协议相对 URL 全部拒绝.

    防止 ?next=https://evil.com 形式的 open redirect 钓鱼.
    """
    from urllib.parse import urlparse
    if not candidate:
        return None
    candidate = candidate.strip()
    # 拒绝绝对 URL (含 scheme 或 netloc), 拒绝协议相对 URL "//evil.com/x"
    if candidate.startswith('//'):
        return None
    parsed = urlparse(candidate)
    if parsed.scheme or parsed.netloc:
        return None
    # 必须以 / 开头, 防 "javascript:..." 等其它伪协议
    if not candidate.startswith('/'):
        return None
    return candidate


# #9: /login 的轻量内存限流。MVP 不引入 Redis/flask-limiter 新依赖(符合"依赖能少则少"),
# 单进程内用滑动窗口足够挡住"接入真实邮件后的邮件轰炸/刷库"。key 为 IP 或邮箱, 值为时间戳列表。
# 注意: 多 worker 部署下各进程独立计数, 规模化时再换集中式限流。
_LOGIN_ATTEMPTS = {}
_LOGIN_WINDOW_SECONDS = 600   # 10 分钟窗口
_LOGIN_MAX_PER_WINDOW = 5     # 同一 IP/邮箱 10 分钟内最多 5 次


def _login_rate_limited(*keys):
    """检查并记录登录尝试; 任一 key 超过窗口上限则返回 True(应拒绝)."""
    now = datetime.now(timezone.utc).timestamp()
    limited = False
    for key in keys:
        if not key:
            continue
        hits = [t for t in _LOGIN_ATTEMPTS.get(key, []) if now - t < _LOGIN_WINDOW_SECONDS]
        if len(hits) >= _LOGIN_MAX_PER_WINDOW:
            limited = True
        hits.append(now)
        _LOGIN_ATTEMPTS[key] = hits
    return limited


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """邮箱或手机号加密码登录。"""
    if _current_user() and request.method == 'GET':
        return redirect(_safe_next_url(request.args.get('next')) or url_for('core.overview'))
    identifier_value = ''
    if request.method == 'POST':
        identifier_value = request.form.get('identifier', '')
        identity_type, identifier = _normalize_identity(identifier_value)
        password = request.form.get('password', '')
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr or '').split(',')[0].strip()
        if not identifier:
            flash('请输入有效的邮箱或手机号', 'danger')
        elif _login_rate_limited(client_ip, identifier):
            flash('请求过于频繁，请稍后再试。', 'danger')
        else:
            identity = AccountIdentity.query.filter_by(identifier=identifier).first()
            # 旧邮箱用户尚未建立身份时，不自动创建凭据，必须走邮箱验证设置密码。
            user = identity.user if identity else None
            credential = PasswordCredential.query.filter_by(user_id=user.id).first() if user else None
            if user and user.status == 'active' and credential and check_password_hash(credential.password_hash, password):
                _start_user_session(user)
                flash('已登录', 'success')
                return redirect(_safe_next_url(request.args.get('next')) or url_for('core.overview'))
            else:
                flash('账号或密码不正确', 'danger')
    return render_template('auth/login.html', identifier=identifier_value)


@bp.route('/invite/<token>')
def organization_invitation_accept(token):
    invitation = _pending_organization_invitation(token)
    if not invitation:
        flash('团队邀请无效、已过期或已被使用', 'danger')
        return redirect(url_for('core.login'))
    session['pending_invitation_token'] = token
    user = _current_user()
    if user:
        return _complete_invitation_for_user(invitation, user)
    existing_identity = AccountIdentity.query.filter_by(identifier=invitation.identifier).first()
    if existing_identity:
        flash('请登录受邀账号后接受团队邀请', 'info')
        return redirect(url_for('core.login', next=url_for('core.organization_invitation_resume')))
    return redirect(url_for('core.register'))


@bp.route('/invite/pending')
def organization_invitation_resume():
    invitation = _pending_organization_invitation(session.get('pending_invitation_token', ''))
    if not invitation:
        session.pop('pending_invitation_token', None)
        flash('团队邀请无效、已过期或已被使用', 'danger')
        return redirect(url_for('core.account', section='organization'))
    user = _current_user()
    if not user:
        return redirect(url_for('core.login', next=request.path))
    return _complete_invitation_for_user(invitation, user)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """提交注册资料并发送邮箱/手机验证码。"""
    if _current_user():
        return redirect(url_for('core.overview'))
    invitation_token = session.get('pending_invitation_token', '')
    invitation = _pending_organization_invitation(invitation_token) if invitation_token else None
    if invitation_token and not invitation:
        session.pop('pending_invitation_token', None)
    form = {'identifier': invitation.identifier if invitation else '', 'display_name': ''}
    if request.method == 'POST':
        form['identifier'] = request.form.get('identifier', '')
        form['display_name'] = request.form.get('display_name', '').strip()
        identity_type, identifier = _normalize_identity(form['identifier'])
        password = request.form.get('password', '')
        if not identifier:
            flash('请输入有效的邮箱或手机号', 'danger')
        elif invitation and identifier != invitation.identifier:
            flash('注册账号必须与团队邀请的邮箱或手机号一致', 'danger')
        elif AccountIdentity.query.filter_by(identifier=identifier).first():
            flash('该邮箱或手机号已注册', 'danger')
        elif identity_type == 'email' and User.query.filter_by(email=identifier).first():
            # 旧账户尚无 AccountIdentity，不能再次注册；通过原邮箱验证后设置密码完成迁移。
            flash('该邮箱已有旧账号，请验证邮箱并设置登录密码', 'warning')
            return redirect(url_for('core.password_setup', identifier=identifier))
        elif _login_rate_limited(f'register:{identifier}'):
            flash('验证码请求过于频繁，请稍后再试', 'danger')
        elif not _valid_password(password):
            flash('密码至少 8 位，并同时包含字母和数字', 'danger')
        elif password != request.form.get('password_confirm', ''):
            flash('两次输入的密码不一致', 'danger')
        else:
            try:
                dev_code = _create_verification_code(identity_type, identifier, 'register', {
                    'password_hash': generate_password_hash(password),
                    'display_name': form['display_name'][:80],
                    'invitation_id': invitation.id if invitation else None,
                })
            except RuntimeError as exc:
                flash(str(exc), 'danger')
                return render_template('auth/register.html', form=form, invitation=invitation)
            return render_template('auth/verify.html', purpose='register', identifier=identifier,
                                   identity_type=identity_type, dev_code=dev_code)
    return render_template('auth/register.html', form=form, invitation=invitation)


@bp.route('/register/verify', methods=['POST'])
def register_verify():
    identity_type, identifier = _normalize_identity(request.form.get('identifier'))
    if not identifier:
        flash('账号标识无效，请重新注册', 'danger')
        return redirect(url_for('core.register'))
    # 验证码页面可能在另一标签页停留较久，落库前必须重新检查新身份和旧用户表。
    if AccountIdentity.query.filter_by(identifier=identifier).first():
        flash('该账号已经注册，请直接登录', 'warning')
        return redirect(url_for('core.login'))
    if identity_type == 'email' and User.query.filter_by(email=identifier).first():
        flash('该邮箱已有旧账号，请验证邮箱并设置登录密码', 'warning')
        return redirect(url_for('core.password_setup', identifier=identifier))
    record = _consume_verification_code(identifier, 'register', request.form.get('code'))
    if not record:
        flash('验证码错误、已过期或尝试次数过多', 'danger')
        return render_template('auth/verify.html', purpose='register', identifier=identifier,
                               identity_type=identity_type, dev_code=None)
    if AccountIdentity.query.filter_by(identifier=identifier).first():
        flash('该账号已经注册，请直接登录', 'warning')
        return redirect(url_for('core.login'))
    if identity_type == 'email' and User.query.filter_by(email=identifier).first():
        flash('该邮箱已有旧账号，请验证邮箱并设置登录密码', 'warning')
        return redirect(url_for('core.password_setup', identifier=identifier))
    # 旧 users.email 不可空；手机号账户使用不可登录、不可展示的内部占位值保持兼容。
    legacy_email = identifier if identity_type == 'email' else f'phone_{_hash_token(identifier)[:20]}@identity.invalid'
    user = User(email=legacy_email, display_name=(record.payload or {}).get('display_name') or None,
                email_verified_at=datetime.now(timezone.utc) if identity_type == 'email' else None)
    invitation_id = (record.payload or {}).get('invitation_id')
    invitation = OrganizationInvitation.query.filter_by(id=invitation_id, status='pending').first() if invitation_id else None
    if invitation_id:
        expires_at = invitation.expires_at if invitation else None
        if not invitation or invitation.identifier != identifier or not expires_at:
            flash('团队邀请已失效，请联系邀请人重新发送', 'danger')
            return redirect(url_for('core.register'))
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= datetime.now(timezone.utc):
            invitation.status = 'expired'
            db.session.commit()
            flash('团队邀请已过期，请联系邀请人重新发送', 'danger')
            return redirect(url_for('core.register'))
    try:
        db.session.add(user)
        db.session.flush()
        db.session.add(AccountIdentity(user_id=user.id, identity_type=identity_type, identifier=identifier,
                                       verified_at=datetime.now(timezone.utc), is_primary=True))
        db.session.add(PasswordCredential(user_id=user.id, password_hash=(record.payload or {})['password_hash']))
        db.session.add(AccountEntitlement(user_id=user.id, can_create_sites=not bool(invitation)))
        if invitation:
            _accept_organization_invitation(invitation, user)
            _write_audit(user, 'organization.invitation.accept',
                         f'接受团队“{invitation.organization.name}”邀请',
                         organization_id=invitation.organization_id,
                         details={'role': invitation.role, 'invitation_id': invitation.id})
        db.session.commit()
    except IntegrityError:
        # 并发注册或旧数据竞争只能转成用户可理解的提示，绝不能暴露数据库调试页。
        db.session.rollback()
        current_app.logger.warning('注册身份发生唯一约束冲突: %s', identifier)
        if identity_type == 'email' and User.query.filter_by(email=identifier).first():
            flash('该邮箱已有账号，请验证邮箱并设置登录密码', 'warning')
            return redirect(url_for('core.password_setup', identifier=identifier))
        flash('该邮箱或手机号已注册，请直接登录', 'warning')
        return redirect(url_for('core.login'))
    _start_user_session(user)
    session.pop('pending_invitation_token', None)
    flash('注册成功', 'success')
    return redirect(_invitation_landing_url(invitation) if invitation else url_for('core.templates_gallery'))


@bp.route('/password/setup', methods=['GET', 'POST'])
def password_setup():
    """旧邮箱账户迁移和忘记密码共用的身份验证入口。"""
    identifier_value = request.args.get('identifier', '').strip()
    if request.method == 'POST':
        identifier_value = request.form.get('identifier', '')
        identity_type, identifier = _normalize_identity(identifier_value)
        user = None
        identity = AccountIdentity.query.filter_by(identifier=identifier).first() if identifier else None
        if identity:
            user = identity.user
        elif identity_type == 'email':
            user = User.query.filter_by(email=identifier).first()
        # 中性反馈只在用户存在时创建验证码，避免泄露注册状态。
        if identifier and _login_rate_limited(f'password-setup:{identifier}'):
            flash('验证码请求过于频繁，请稍后再试', 'danger')
            return render_template('auth/password_setup.html', identifier=identifier_value)
        try:
            dev_code = _create_verification_code(identity_type, identifier, 'password_setup', {'user_id': user.id}) if user else None
        except RuntimeError as exc:
            flash(str(exc), 'danger')
            return render_template('auth/password_setup.html', identifier=identifier_value)
        # 无论账号是否存在都进入同一页面，避免通过响应差异枚举账号。
        flash('如果该账号存在，验证码已发送', 'info')
        return render_template('auth/verify.html', purpose='password_setup', identifier=identifier or identifier_value,
                               identity_type=identity_type or 'email', dev_code=dev_code, set_password=True)
    return render_template('auth/password_setup.html', identifier=identifier_value)


@bp.route('/password/setup/verify', methods=['POST'])
def password_setup_verify():
    identity_type, identifier = _normalize_identity(request.form.get('identifier'))
    password = request.form.get('password', '')
    if not identifier or not _valid_password(password) or password != request.form.get('password_confirm', ''):
        flash('验证码或密码格式不正确', 'danger')
        return redirect(url_for('core.password_setup'))
    record = _consume_verification_code(identifier, 'password_setup', request.form.get('code'))
    if not record:
        flash('验证码错误、已过期或尝试次数过多', 'danger')
        return redirect(url_for('core.password_setup'))
    user = User.query.get((record.payload or {}).get('user_id'))
    if not user:
        abort(400)
    identity = AccountIdentity.query.filter_by(identifier=identifier).first()
    if not identity:
        identity = AccountIdentity(user_id=user.id, identity_type=identity_type, identifier=identifier,
                                   verified_at=datetime.now(timezone.utc), is_primary=True)
        db.session.add(identity)
    credential = PasswordCredential.query.filter_by(user_id=user.id).first()
    if credential:
        credential.password_hash = generate_password_hash(password)
        credential.password_changed_at = datetime.now(timezone.utc)
    else:
        db.session.add(PasswordCredential(user_id=user.id, password_hash=generate_password_hash(password)))
    UserSession.query.filter_by(user_id=user.id, revoked_at=None).update({'revoked_at': datetime.now(timezone.utc)})
    db.session.commit()
    _start_user_session(user)
    flash('登录密码已设置', 'success')
    return redirect(url_for('core.overview'))


@bp.route('/auth/magic/<token>')
def magic_login(token):
    """旧用户迁移期兼容入口；新登录页不再创建魔法链接。"""
    now = datetime.now(timezone.utc)
    login_token = LoginToken.query.filter_by(token_hash=_hash_token(token)).first()
    if not login_token or login_token.used_at:
        flash('登录链接无效或已使用，请重新获取。', 'danger')
        return redirect(url_for('core.login'))
    expires_at = login_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < now:
        flash('登录链接已过期，请重新获取。', 'danger')
        return redirect(url_for('core.login'))

    user = User.query.get(login_token.user_id) or User.query.filter_by(email=login_token.email).first()
    if not user or user.status != 'active':
        flash('账号不可用，请联系管理员。', 'danger')
        return redirect(url_for('core.login'))

    login_token.used_at = now
    user.email_verified_at = user.email_verified_at or now
    user.last_login_at = now
    db.session.commit()

    _start_user_session(user)
    flash('已登录', 'success')
    if user.role == 'admin':
        if Site.query.filter(Site.soft_deleted_at.is_(None)).first():
            return redirect(url_for('core.overview'))
        else:
            flash("尚无站点，请先从模板库创建站点", "warning")
            return redirect(url_for('core.templates_gallery'))
    if Site.query.filter_by(owner_id=user.id).filter(Site.soft_deleted_at.is_(None)).first():
        return redirect(url_for('core.overview'))
    return redirect(url_for('core.templates_gallery'))


@bp.route('/logout', methods=['POST'])
def logout():
    raw_token = session.get('auth_session_token')
    if raw_token:
        login_session = UserSession.query.filter_by(token_hash=_hash_token(raw_token)).first()
        if login_session:
            login_session.revoked_at = datetime.now(timezone.utc)
            db.session.commit()
    session.clear()
    flash('已退出登录', 'success')
    return redirect(url_for('core.login'))


@bp.route('/assets/<path:filename>')
def site_asset(filename):
    """预览/后台共用的站点上传资源入口。预览页免登录，资源请求也免登录。

    通过 session 定位资源目录，确保预览页里 <img src="/assets/...">
    和 CSS 中 url(/assets/...) 直接访问而不被拦到登录页。
    静态导出时由 output/assets 直接承载。
    """
    assets_root = None
    referer = request.headers.get('Referer', '')
    m = re.search(r'/preview(?:/(?:site|or_build))?/(\d+)', referer)
    if m:
        site = Site.query.get(int(m.group(1)))
        if site:
            site_assets = Path(current_app.config['SITES_DIR']) / str(site.id) / 'assets'
            if (site_assets / filename).exists():
                return _safe_send_from_directory(site_assets, filename)

    site_id = session.get('current_site_id')
    if site_id is not None:
        site = Site.query.get(int(site_id))
        if site:
            site_assets = Path(current_app.config['SITES_DIR']) / str(site.id) / 'assets'
            if (site_assets / filename).exists():
                return _safe_send_from_directory(site_assets, filename)

    # 1. 模板预览 session（最优先：CSS 背景图 Referer 是 main.css，不包含 /preview/）
    tpl_name = session.get('current_template_preview')
    if tpl_name:
        tpl_assets = Path(current_app.config['OUTPUT_DIR']) / '_preview' / tpl_name / 'assets'
        if tpl_assets.exists():
            assets_root = tpl_assets

    # 2. 站点预览 / 管理后台 session
    if assets_root is None:
        site_id = session.get('current_site_id')
        if site_id is not None:
            site = Site.query.get(int(site_id))
            if site:
                assets_root = Path(current_app.config['SITES_DIR']) / str(site.id) / 'assets'

    # 3. Referer 兜底（清除 session 后首次请求等极端情况）
    referer = request.headers.get('Referer', '')
    if assets_root is None:
        m = re.search(r'/templates/([a-zA-Z0-9_-]+)/preview/', referer)
        if m:
            tpl_assets = Path(current_app.config['OUTPUT_DIR']) / '_preview' / m.group(1) / 'assets'
            if tpl_assets.exists():
                assets_root = tpl_assets
    if assets_root is None:
        m = re.search(r'/preview(?:/(?:site|or_build))?/(\d+)', referer)
        if m:
            site = Site.query.get(int(m.group(1)))
            if site:
                assets_root = Path(current_app.config['SITES_DIR']) / str(site.id) / 'assets'

    # 4. 最终兜底
    if assets_root is None:
        site = Site.query.order_by(Site.id.desc()).first()
        if site:
            assets_root = Path(current_app.config['SITES_DIR']) / str(site.id) / 'assets'

    if assets_root is None:
        abort(404, '资源不存在')
    return _safe_send_from_directory(assets_root, filename)


def _media_package_assets_root():
    """Resolve the current site's media package root for admin and preview requests."""
    assets_root = None
    site_id = session.get('current_site_id')
    if site_id is not None:
        site = Site.query.get(int(site_id))
        if site:
            assets_root = Path(current_app.config['SITES_DIR']) / str(site.id) / 'assets'

    referer = request.headers.get('Referer', '')
    if assets_root is None:
        m = re.search(r'/preview(?:/(?:site|or_build))?/(\d+)', referer)
        if m:
            site = Site.query.get(int(m.group(1)))
            if site:
                assets_root = Path(current_app.config['SITES_DIR']) / str(site.id) / 'assets'

    if assets_root is None:
        site = Site.query.order_by(Site.id.desc()).first()
        if site:
            assets_root = Path(current_app.config['SITES_DIR']) / str(site.id) / 'assets'

    if assets_root is None:
        abort(404, '网页包不存在')
    return assets_root / 'media-packages'


@bp.route('/media-packages/<package_name>/')
def media_package_index(package_name):
    package_name = secure_filename(package_name or '')
    if not package_name:
        abort(404, '网页包不存在')
    packages_root = _media_package_assets_root()
    package_dir = (packages_root / package_name).resolve()
    try:
        package_dir.relative_to(packages_root.resolve())
    except ValueError:
        abort(403, '非法路径')
    if not (package_dir / 'index.html').exists():
        abort(404, '网页包不存在')
    return _safe_send_from_directory(package_dir, 'index.html')


@bp.route('/media-packages/<package_name>/<path:filename>')
def media_package_asset(package_name, filename):
    package_name = secure_filename(package_name or '')
    if not package_name:
        abort(404, '网页包不存在')
    packages_root = _media_package_assets_root()
    package_dir = (packages_root / package_name).resolve()
    try:
        package_dir.relative_to(packages_root.resolve())
    except ValueError:
        abort(403, '非法路径')
    return _safe_send_from_directory(package_dir, filename)


@bp.errorhandler(403)
def forbidden(error):
    """区分无访问权与只读写入拦截，避免向后台面板输出默认英文错误页。"""
    description = getattr(error, 'description', '') or '当前账号无权执行此操作'
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest' \
            or request.accept_mimetypes.best == 'application/json':
        return jsonify({'ok': False, 'error': description, 'code': 'read_only' if '只读' in description else 'forbidden'}), 403
    return render_template('dashboard/permission_denied.html', message=description), 403


@bp.errorhandler(404)
def not_found(error):
    """捕获 404，无站点时重定向到模板库."""
    desc = error.description if hasattr(error, 'description') else str(error)
    if '尚无站点' in str(desc):
        flash("尚无站点，请先从模板库创建站点", "warning")
        return redirect(url_for('core.templates_gallery'))
    return f"<h1>404 Not Found</h1><p>{desc}</p>", 404


@bp.route('/')
def index():
    return _render_site_overview()


def _render_site_overview():
    user, site = _current_context()
    settings = read_yaml(site.id, 'settings.yaml') or {}
    meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    meta = _yaml.safe_load(meta_path.read_text(encoding='utf-8')) or {} if meta_path.exists() else {}
    menu = menu_lib.ensure_home(menu_lib.normalize_for_render(
        menu_lib.upgrade_old_format(settings.get('menu') or [], meta.get('datasets', []))
    ))

    def count_pages(items):
        return sum(
            (1 if item.get('type') in {'home', 'page', 'list'} else 0)
            + count_pages(item.get('children') or [])
            for item in (items or []) if isinstance(item, dict)
        )

    dataset_keys = {item.get('target') for item in menu_lib.collect_list_targets(menu) if item.get('target')}
    overview_storage_lang = _storage_lang(site, site.default_language, site.default_language)
    content_count = sum(
        len(datasets.load(site.id, key, lang=overview_storage_lang) or [])
        for key in dataset_keys
    )
    page_count = count_pages(menu)
    enabled_language_count = len(site.enabled_languages or [site.default_language])
    setup_checks = {
        'site': bool(site.name and site.slug),
        'pages': page_count > 1,
        'content': content_count > 0,
        'published': site.status == 'published',
    }
    setup_completed = sum(setup_checks.values())
    setup_percent = round(setup_completed * 100 / len(setup_checks))
    recent_logs = AuditLog.query.filter_by(site_id=site.id).order_by(
        AuditLog.created_at.desc(), AuditLog.id.desc()
    ).limit(5).all()
    return render_template('dashboard/overview.html', user=user, site=site, active='overview',
                           page_count=page_count, content_count=content_count,
                           enabled_language_count=enabled_language_count,
                           setup_checks=setup_checks, setup_completed=setup_completed,
                           setup_percent=setup_percent,
                           recent_logs=recent_logs,
                           initial_panel_collapsed=False)


@bp.route('/overview')
def overview():
    return _render_site_overview()


@bp.route('/workbench')
def workbench():
    user, site = _current_context()
    return render_template('base.html', user=user, site=site, active='',
                           initial_panel_collapsed=True)


def _content_catalog(site, lang, default_lang):
    """汇总站点菜单中的列表数据集，供内容中心统一检索。

    内容中心只暴露菜单中明确声明为 list 的数据集，避免把内部配置型 YAML
    （例如旧版 products/posts 兼容数据）误当成可编辑内容展示给用户。
    """
    settings = read_yaml(site.id, 'settings.yaml') or {}
    meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    meta = _yaml.safe_load(meta_path.read_text(encoding='utf-8')) if meta_path.exists() else {}
    raw_menu = menu_lib.upgrade_old_format(settings.get('menu') or [], meta.get('datasets', []))
    menu_labels = (settings.get('menu_labels') or {}).get(lang, {}) or {}
    storage_lang = _storage_lang(site, lang, default_lang)
    source_storage_lang = _storage_lang(site, default_lang, default_lang)
    catalog = []

    def localized_label(item):
        key = item.get('target') or ('__home__' if item.get('type') == 'home' else item.get('url'))
        return menu_labels.get(key) or item.get('label') or item.get('target') or '未命名'

    def walk(items, parents=None):
        parents = parents or []
        for item in items or []:
            if not isinstance(item, dict):
                continue
            item_type = item.get('type')
            target = str(item.get('target') or '').strip()
            label = localized_label(item)
            next_parents = parents
            if item_type == 'group':
                next_parents = parents + [{'label': label, 'target': target}]
            if item_type == 'list' and target:
                # 内容中心是索引入口，浏览列表不能顺带迁移或改写站点文件。
                page = read_yaml(site.id, f'pages/{target}.yaml', default={}) or {}
                templates = _detail_templates_for_page(page, target, label)
                default_template_id = _default_detail_template_id(page, target, label)
                rows = datasets.load(site.id, target, lang=storage_lang)
                if storage_lang and not rows:
                    rows = datasets.load(site.id, target, lang=source_storage_lang)
                # 未显式选择模板的旧内容实际使用默认模板，统计时也必须计入。
                for template in templates:
                    template_id = str(template.get('id') or '')
                    template['content_usage'] = sum(
                        1 for row in (rows or [])
                        if str(row.get('template_id') or default_template_id) == template_id
                    )
                parent_key = parents[0]['target'] if parents else ''
                category = parents[0]['label'] if parents else ''
                path_parts = [p.get('target') for p in parents if p.get('target')] + [target]
                catalog.append({
                    'key': target,
                    'label': label,
                    'category': category,
                    'parent_key': parent_key,
                    'path': '/'.join(path_parts),
                    'items': rows or [],
                    'templates': templates,
                    'default_template_id': default_template_id,
                })
            walk(item.get('children') or [], next_parents)

    walk(raw_menu)
    return catalog


@bp.route('/content/workspace')
def content_workspace():
    """全站列表详情内容的统一查找、新建和模板入口。"""
    user, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    mode = request.args.get('mode', 'list').strip()
    if mode not in ('list', 'new', 'templates'):
        mode = 'list'
    catalog = _content_catalog(site, lang, default_lang)
    # 左侧分类树保留菜单顺序；有上级的聚合为可展开节点，独立列表直接作为一级节点。
    content_facets = []
    facet_groups = {}
    for entry in catalog:
        parent_key = entry.get('parent_key') or ''
        if not parent_key:
            content_facets.append({
                'type': 'dataset', 'key': entry['key'], 'label': entry['label'],
                'count': len(entry.get('items') or []), 'entry': entry,
            })
            continue
        node = facet_groups.get(parent_key)
        if node is None:
            node = {
                'type': 'group', 'key': parent_key, 'label': entry['category'],
                'count': 0, 'children': [],
            }
            facet_groups[parent_key] = node
            content_facets.append(node)
        node['children'].append(entry)
        node['count'] += len(entry.get('items') or [])
    template_names = {
        f"{entry['key']}:{tpl.get('id')}": tpl.get('name') or tpl.get('id')
        for entry in catalog for tpl in entry.get('templates') or [] if isinstance(tpl, dict)
    }
    total_items = sum(len(entry.get('items') or []) for entry in catalog)
    requested_dataset = request.args.get('dataset', '').strip()
    initial_dataset = requested_dataset if any(entry['key'] == requested_dataset for entry in catalog) else ''
    return render_template('dashboard/content_workspace.html',
                           user=user, site=site, active=f'content_{mode}', mode=mode,
                           catalog=catalog, content_facets=content_facets,
                           template_names=template_names,
                           total_items=total_items, initial_dataset=initial_dataset,
                           current_lang=lang,
                           languages=languages, default_lang=default_lang)


@bp.route('/content/create', methods=['POST'])
def content_create():
    """验证新建向导选择并进入临时编辑态；此时不写入数据集。"""
    _, site = _current_context()
    lang, _, default_lang = _get_panel_lang(site)
    dataset_key = request.form.get('dataset_key', '').strip()
    template_id = request.form.get('template_id', '').strip()
    catalog = _content_catalog(site, lang, default_lang)
    entry = next((item for item in catalog if item.get('key') == dataset_key), None)
    if not entry:
        return jsonify({'ok': False, 'error': '请选择有效的内容分类'}), 400
    valid_template_ids = {str(tpl.get('id') or '') for tpl in entry.get('templates') or []}
    if template_id not in valid_template_ids:
        return jsonify({'ok': False, 'error': '请选择有效的详情模板'}), 400
    return jsonify({
        'ok': True,
        'item_id': 0,
        'dataset_key': dataset_key,
        'editor_url': url_for('core.content_item_workspace', dataset_key=dataset_key, item_id=0,
                              template_id=template_id, site=site.id, lang=lang),
        'preview_path': entry.get('path') or dataset_key,
        'slug': '',
    })


@bp.route('/content/<path:dataset_key>/<int:item_id>/duplicate', methods=['POST'])
def content_duplicate(dataset_key, item_id):
    """进入临时副本编辑态；用户保存前不写入数据集。"""
    _validate_key(dataset_key)
    _, site = _current_context()
    lang, _, default_lang = _get_panel_lang(site)
    catalog = _content_catalog(site, lang, default_lang)
    entry = next((entry for entry in catalog if entry.get('key') == dataset_key), None)
    if not entry:
        return jsonify({'ok': False, 'error': '内容分类不存在'}), 404
    storage_lang = _storage_lang(site, lang, default_lang)
    items = datasets.load(site.id, dataset_key, lang=storage_lang)
    source = next((item for item in items if item.get('id') == item_id), None)
    if not source:
        return jsonify({'ok': False, 'error': '内容不存在'}), 404
    template_id = str(source.get('template_id') or entry.get('default_template_id') or '')
    valid_template_ids = {str(tpl.get('id') or '') for tpl in entry.get('templates') or []}
    if template_id not in valid_template_ids:
        template_id = str(entry.get('default_template_id') or '')
    if template_id not in valid_template_ids:
        return jsonify({'ok': False, 'error': '该内容没有可用的详情模板'}), 400
    return jsonify({
        'ok': True,
        'item_id': 0,
        'editor_url': url_for(
            'core.content_item_workspace', dataset_key=dataset_key, item_id=0,
            template_id=template_id, copy_from=item_id, site=site.id, lang=lang,
        ),
    })


@bp.route('/content/<path:dataset_key>/<int:item_id>/delete', methods=['POST'])
def content_delete(dataset_key, item_id):
    """从内容中心删除条目并返回 JSON。"""
    _validate_key(dataset_key)
    _, site = _current_context()
    lang, _, default_lang = _get_panel_lang(site)
    catalog = _content_catalog(site, lang, default_lang)
    if not any(entry.get('key') == dataset_key for entry in catalog):
        return jsonify({'ok': False, 'error': '内容分类不存在'}), 404
    storage_lang = _storage_lang(site, lang, default_lang)
    if not datasets.find(site.id, dataset_key, item_id, lang=storage_lang):
        return jsonify({'ok': False, 'error': '内容不存在'}), 404
    datasets.remove(site.id, dataset_key, item_id, lang=storage_lang)
    return jsonify({'ok': True})


@bp.route('/company/workspace')
def company_workspace():
    """Open company settings in the center workspace instead of the side panel."""
    user, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    settings = read_yaml(site.id, 'settings.yaml', default={}, lang=lang) or {}
    company_key = _lang_key('company', site, lang, default_lang)
    contact_key = _lang_key('contact', site, lang, default_lang)
    current_company = _merge_settings_section(settings.get('company'), settings.get(company_key))
    source_company = settings.get('company', {})
    current_contact = _merge_settings_section(settings.get('contact'), settings.get(contact_key))
    source_contact = settings.get('contact', {})
    return render_template('dashboard/settings_workspace.html',
                           title='公司信息',
                           panel_template='dashboard/panel_company.html',
                           user=user, site=site, active='company',
                           company=current_company,
                           contact=current_contact,
                           source_company=source_company,
                           source_contact=source_contact,
                           current_lang=lang,
                           languages=languages,
                           default_lang=default_lang,
                           settings_workspace=True)


@bp.route('/theme/workspace')
def theme_workspace():
    """Open theme settings in the center workspace instead of the side panel."""
    user, site = _current_context()
    settings = read_yaml(site.id, 'settings.yaml', default={}) or {}
    tpl_meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    tpl_meta = _yaml.safe_load(tpl_meta_path.read_text(encoding='utf-8')) if tpl_meta_path.exists() else {}
    default_theme = tpl_meta.get('default_theme') or {}
    theme = settings.get('theme') or {}
    return render_template('dashboard/settings_workspace.html',
                           title='主题颜色',
                           panel_template='dashboard/panel_theme.html',
                           user=user, site=site, active='theme',
                           theme=theme,
                           default_theme=default_theme,
                           settings_workspace=True)


@bp.route('/settings/basic')
def basic_settings():
    """Company and theme settings in one side panel with tabs."""
    user, site = _current_context()
    settings = read_yaml(site.id, 'settings.yaml') or {}
    lang, languages, default_lang = _get_panel_lang(site)
    company_key = _lang_key('company', site, lang, default_lang)
    contact_key = _lang_key('contact', site, lang, default_lang)
    current_company = _merge_settings_section(settings.get('company'), settings.get(company_key))
    current_contact = _merge_settings_section(settings.get('contact'), settings.get(contact_key))
    source_company = settings.get('company', {})
    source_contact = settings.get('contact', {})

    tpl_meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    tpl_meta = _yaml.safe_load(tpl_meta_path.read_text(encoding='utf-8')) if tpl_meta_path.exists() else {}
    default_theme = tpl_meta.get('default_theme') or {}
    theme = settings.get('theme') or {}
    tab = request.args.get('tab') or 'company'
    if tab not in ('company', 'theme'):
        tab = 'company'

    # 中间栏嵌入模式：渲染无外壳的独立页面。
    if request.args.get('embed') == '1':
        return render_template('dashboard/basic_settings_embed.html',
                               user=user, site=site,
                               company=current_company,
                               contact=current_contact,
                               source_company=source_company,
                               source_contact=source_contact,
                               theme=theme,
                               default_theme=default_theme,
                               admin_settings=settings.get('admin') or {},
                               current_lang=lang,
                               languages=languages,
                               default_lang=default_lang,
                               basic_settings_tab=tab,
                               active='basic_settings')

    return render_template('dashboard/panel_basic_settings.html',
                           user=user, site=site,
                           company=current_company,
                           contact=current_contact,
                           source_company=source_company,
                           source_contact=source_contact,
                           theme=theme,
                           default_theme=default_theme,
                           admin_settings=settings.get('admin') or {},
                           current_lang=lang,
                           languages=languages,
                           default_lang=default_lang,
                           basic_settings_tab=tab,
                           active='basic_settings')


@bp.route('/media')
def media():
    user, site = _current_context()
    files = list_media_files(site.id)
    if request.args.get('_fragment'):
        return render_template('dashboard/panel_media.html',
                               user=user, site=site, files=files)
    return render_template('dashboard/media.html',
                           user=user, site=site, files=files, active='media')


@bp.route('/media/workspace')
def media_workspace():
    user, site = _current_context()
    files = list_media_files(site.id)
    return render_template('dashboard/media_workspace.html',
                           user=user, site=site, files=files, active='media')


@bp.route('/api/media/references')
def api_media_references():
    _, site = _current_context()
    name = request.args.get('filename') or request.args.get('name') or ''
    if not name:
        return jsonify({'error': '缺少文件名'}), 400
    refs = find_media_references(site.id, name)
    return jsonify({'filename': name, 'refs': refs, 'count': len(refs)})


@bp.route('/api/site/pages')
def api_site_pages():
    """返回当前站点所有可链接的页面（菜单项 + pages/ 目录下的孤儿 YAML）。

    前端 RTE 链接插入器使用，用于在「本站页面」标签页中展示可选目标。
    """
    _, site = _current_context()
    settings = read_yaml(site.id, 'settings.yaml') or {}
    raw_menu = settings.get('menu') or []
    pages_dir = lang_root(site.id) if False else None

    # 从菜单树中收集所有有 URL 的页面项
    seen_keys = set()
    pages = []

    def collect(items):
        if not isinstance(items, list):
            return
        for it in items:
            if not isinstance(it, dict):
                continue
            t = it.get('type')
            if t in ('home', 'page', 'list'):
                key = it.get('target', '') or 'home'
                if t == 'home':
                    key = 'home'
                if key and key not in seen_keys:
                    seen_keys.add(key)
                    label = it.get('label') or key
                    url = menu_lib.url_of(it)
                    pages.append({'key': key, 'label': label, 'url': url, 'type': t})
            collect(it.get('children') or [])

    # 升级旧格式后收集
    meta = {}
    template_meta_file = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    if template_meta_file.exists():
        try:
            meta = _yaml.safe_load(template_meta_file.read_text(encoding='utf-8')) or {}
        except Exception:
            pass
    upgraded = menu_lib.upgrade_old_format(raw_menu, meta.get('datasets', []))
    collect(upgraded)

    # 补充 pages/ 目录中未被菜单覆盖的孤儿 YAML（兼容手动创建的页面文件）
    try:
        for file in list_yaml_files(site.id, 'pages'):
            key = file.stem
            if key not in seen_keys:
                seen_keys.add(key)
                page_data = read_yaml(site.id, f'pages/{file.name}') or {}
                label = page_data.get('title') or page_data.get('label') or key
                url = f'/{key}' if key != 'home' else '/'
                pages.append({'key': key, 'label': label, 'url': url, 'type': 'page'})
    except Exception:
        pass

    return jsonify({'pages': pages})


@bp.route('/api/media/upload', methods=['POST'])
def api_media_upload():
    _, site = _current_context()
    upload = request.files.get('file')
    if not upload or not upload.filename:
        return jsonify({'error': '请选择文件'}), 400
    original = secure_filename(upload.filename)
    suffix = original.rsplit('.', 1)[-1].lower() if '.' in original else ''
    try:
        if suffix == 'zip':
            # 根目录有 index.html → 网页包；否则降级为普通文件。
            if media_service.uploaded_zip_has_index(upload):
                result = _save_media_package(site.id, upload)
                return jsonify({'ok': True, **result})
            # 不是网页包 → 继续往下走普通文件上传流程

        if suffix in ALLOWED_IMAGE_EXTENSIONS or suffix in ALLOWED_VIDEO_EXTENSIONS:
            url = _save_uploaded_media(site.id, upload, prefix='media')
        else:
            url = _save_any_file(site.id, upload, prefix='media')
        if not url:
            return jsonify({'error': '文件上传失败或类型不支持'}), 400
        filename = url.rsplit('/', 1)[-1]
        files = [item for item in list_media_files(site.id) if item.get('api_name') == filename]
        payload = files[0] if files else {'name': filename, 'api_name': filename, 'url': url}
        return jsonify({'ok': True, **payload})
    except Exception as exc:
        current_app.logger.warning('media upload failed: %s', exc)
        return jsonify({'error': str(exc)}), 400


@bp.route('/api/media/rename', methods=['POST'])
def api_media_rename():
    _, site = _current_context()
    data = request.get_json(silent=True) or request.form
    old_name = (data.get('old_name') or data.get('filename') or '').strip()
    new_name = (data.get('new_name') or '').strip()
    if not old_name or not new_name:
        return jsonify({'error': '缺少文件名'}), 400
    refs = find_media_references(site.id, old_name)
    try:
        new_api_name = rename_media_file(site.id, old_name, new_name)
    except Exception as exc:
        current_app.logger.warning('media rename failed: %s', exc)
        return jsonify({'error': str(exc)}), 400
    if is_media_package_token(new_api_name):
        package_name = media_package_name_from_token(new_api_name)
        return jsonify({
            'ok': True,
            'name': package_name,
            'api_name': new_api_name,
            'url': f'/media-packages/{package_name}/',
            'entry_url': f'/media-packages/{package_name}/',
            'category': 'package',
            'updated_refs': refs,
            'count': len(refs),
        })
    return jsonify({
        'ok': True,
        'name': new_api_name,
        'api_name': new_api_name,
        'url': f'/assets/uploads/{new_api_name}',
        'updated_refs': refs,
        'count': len(refs),
    })


@bp.route('/api/media/delete', methods=['POST'])
def api_media_delete():
    _, site = _current_context()
    data = request.get_json(silent=True) or request.form
    name = (data.get('filename') or data.get('name') or '').strip()
    if not name:
        return jsonify({'error': '缺少文件名'}), 400
    refs = find_media_references(site.id, name)
    if refs:
        return jsonify({'ok': False, 'error': '文件已被引用，不能删除', 'refs': refs, 'count': len(refs)}), 409
    try:
        delete_media_file(site.id, name)
    except Exception as exc:
        current_app.logger.warning('media delete failed: %s', exc)
        return jsonify({'error': str(exc)}), 400
    return jsonify({'ok': True})


def _as_items(raw):
    """把数据集 YAML 标准化成条目列表，健康检查只读不改原数据。"""
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        items = raw.get('items', [])
        return items if isinstance(items, list) else []
    return []


def _plain_text(value):
    """把模块字段压成短文本，供 SEO 简介自动生成使用。"""
    if value is None:
        return ''
    if isinstance(value, str):
        return re.sub(r'<[^>]+>', ' ', value).strip()
    if isinstance(value, (int, float)):
        return str(value)
    return ''


def _auto_page_description(page):
    """从页面模块内容生成简介。

    这不是让店主手写 SEO，而是先从已有业务内容里抽取摘要；店主觉得不合适
    时再手动改写。后续接入真正 AI 文案接口时，只需要替换这个函数。
    """
    if not isinstance(page, dict):
        return ''
    parts = []
    for module in page.get('modules') or []:
        data = module.get('data') if isinstance(module, dict) else {}
        if not isinstance(data, dict):
            continue
        for key in ('desc', 'subtitle', 'summary', 'description', 'body', 'content', 'title'):
            text = _plain_text(data.get(key))
            if text:
                parts.append(text)
        if len(' '.join(parts)) >= 180:
            break
    text = re.sub(r'\s+', ' ', ' '.join(parts)).strip()
    return text[:180].rstrip()


def _page_text_for_seo(page):
    """收集页面核心文本，作为 AI 生成 SEO 简介的上下文。"""
    if not isinstance(page, dict):
        return ''
    parts = []
    for module in page.get('modules') or []:
        data = module.get('data') if isinstance(module, dict) else {}
        if not isinstance(data, dict):
            continue
        for key in ('title', 'desc', 'subtitle', 'summary', 'description', 'body', 'content'):
            text = _plain_text(data.get(key))
            if text:
                parts.append(text)
        for value in data.values():
            if isinstance(value, list):
                for item in value[:8]:
                    if not isinstance(item, dict):
                        continue
                    for key in ('title', 'desc', 'text', 'summary'):
                        text = _plain_text(item.get(key))
                        if text:
                            parts.append(text)
    return re.sub(r'\s+', ' ', ' '.join(parts)).strip()[:2200]


def _dataset_items(raw):
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        items = raw.get('items')
        return items if isinstance(items, list) else []
    return []


def _detail_item_text_for_seo(item):
    if not isinstance(item, dict):
        return ''
    parts = []
    for key in ('seo_title', 'title', 'name', 'seo_description', 'summary', 'description', 'excerpt', 'body', 'content'):
        text = _plain_text(item.get(key))
        if text:
            parts.append(text)
    return re.sub(r'\s+', ' ', ' '.join(parts)).strip()[:2200]


def _seo_status(description, auto_desc):
    if description:
        return 'ok', '已设置', '使用手动简介'
    if auto_desc:
        return 'auto', '可自动生成', '可从页面内容生成简介'
    return 'warn', '缺少内容', '页面内容不足，建议手动填写'


def _seo_page_score(title, description, auto_desc):
    """按可解释的页面内容完整度换算为 1～5 分。"""
    title_len = len(_plain_text(title))
    description_len = len(_plain_text(description))
    score = 1
    if title_len:
        score += 1
    if 10 <= title_len <= 60:
        score += 1
    if description or auto_desc:
        score += 1
    if 50 <= description_len <= 180:
        score += 1
    return min(score, 5)


def _seo_row_for_page(site, lang, page_key, title, page, row_id=None, depth=0, parent_id='', url_path=''):
    page = page if isinstance(page, dict) else {}
    auto_desc = _auto_page_description(page)
    description = page.get('description') or ''
    status, status_label, status_detail = _seo_status(description, auto_desc)
    row_id = row_id or f'page:{page_key}'
    return {
        'id': row_id,
        'key': page_key,
        'type': 'page',
        'kind': 'page',
        'depth': depth,
        'parent_id': parent_id,
        'url_path': url_path,
        'menu_label': title or page_key,  # 菜单原始标签，不受 SEO 标题覆盖影响
        'title': page.get('title') or title or page_key,
        'description': description,
        'auto_description': auto_desc,
        'status': status,
        'status_label': status_label,
        'status_detail': status_detail,
        'score': _seo_page_score(page.get('title') or title or page_key, description, auto_desc),
        'save_url': url_for('core.seo_page_update', page_key=page_key, site=site.id, lang=lang),
        'generate_url': url_for('core.seo_page_generate', page_key=page_key, site=site.id, lang=lang),
    }


def _seo_row_for_detail(site, lang, dataset_key, item, depth=0, parent_id='', url_path=''):
    item = item if isinstance(item, dict) else {}
    slug = item.get('slug') or item.get('id') or ''
    title = item.get('seo_title') or item.get('title') or item.get('name') or str(slug) or '未命名详情页'
    description = item.get('seo_description') or ''
    auto_desc = _plain_text(item.get('summary') or item.get('description') or item.get('excerpt') or item.get('body') or item.get('content'))[:180].rstrip()
    status, status_label, status_detail = _seo_status(description, auto_desc)
    row_id = f'detail:{dataset_key}:{slug}'
    return {
        'id': row_id,
        'key': str(slug),
        'type': 'detail',
        'kind': 'detail',
        'dataset_key': dataset_key,
        'depth': depth,
        'parent_id': parent_id,
        'url_path': url_path,
        'title': title,
        'description': description,
        'auto_description': auto_desc,
        'status': status,
        'status_label': status_label,
        'status_detail': status_detail,
        'score': _seo_page_score(title, description, auto_desc),
        'save_url': url_for('core.seo_detail_update', dataset_key=dataset_key, item_key=slug, site=site.id, lang=lang),
        'generate_url': url_for('core.seo_detail_generate', dataset_key=dataset_key, item_key=slug, site=site.id, lang=lang),
    }


def _seo_page_rows(site, lang, settings, pages, data, meta):
    """返回 SEO 工作区页面行，按菜单树保留层级，包含列表详情页。"""
    tpl_html_dir = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'templates'
    menu_items = menu_lib.ensure_home(
        menu_lib.normalize_for_render(
            menu_lib.upgrade_old_format(settings.get('menu') or [], meta.get('datasets', []))
        )
    )
    rows = []
    seen = set()

    def add_page_row(page_key, label, item_type='page', depth=0, parent_id='', url_path=''):
        if not page_key or page_key in seen or page_key not in pages:
            return ''
        seen.add(page_key)
        row_id = f'page:{page_key}'
        row = _seo_row_for_page(site, lang, page_key, label, pages.get(page_key), row_id=row_id, depth=depth, parent_id=parent_id, url_path=url_path)
        row['type'] = item_type
        rows.append(row)
        return row_id

    # group ID 计数器，确保同标签的多个 group 不会碰撞
    _group_seq = [0]

    def add_group_row(group_key, label, depth=0, parent_id='', url_path=''):
        """为 group 类型菜单生成折叠节点行（无对应页面，仅用于展开/折叠子项）。"""
        _group_seq[0] += 1
        row_id = f'group:{group_key}:{_group_seq[0]}'
        rows.append({
            'id': row_id,
            'key': group_key,
            'type': 'group',
            'kind': 'group',
            'depth': depth,
            'parent_id': parent_id,
            'url_path': url_path,
            'menu_label': label or group_key,
            'title': label or group_key,
            'description': '',
            'auto_description': '',
            'status': 'ok',
            'status_label': '',
            'status_detail': '',
            'score': 0,
            'save_url': '',
            'generate_url': '',
        })
        return row_id

    def walk(items, depth=0, parent_id='', parent_path=''):
        for item in items or []:
            if not isinstance(item, dict):
                continue
            item_type = item.get('type')
            target = item.get('target') or ''
            label = item.get('label') or target or item.get('url') or ''
            # 计算当前项的 URL 路径（与 collect_render_tasks 保持一致）
            if parent_path and target:
                item_path = f'{parent_path}/{target}'
            elif target:
                item_path = target
            else:
                item_path = parent_path
            # 子菜单的父路径：page/list/group 传递其 target
            child_parent = parent_path
            if item_type in ('page', 'list', 'group') and target:
                child_parent = item_path
            # link 类型是外链，不对应具体页面，跳过
            if item_type == 'link':
                if item.get('children'):
                    walk(item.get('children') or [], depth=depth, parent_id=parent_id, parent_path=parent_path)
                continue
            # group 是容器（如"产品"），生成可折叠节点，子页面挂在它下面
            if item_type == 'group':
                group_url_path = f'/{item_path}/' if item_path else '/'
                row_id = add_group_row(
                    target, label, depth=depth, parent_id=parent_id,
                    url_path=group_url_path
                )
                if item.get('children'):
                    walk(item.get('children') or [], depth=depth + 1, parent_id=row_id, parent_path=child_parent)
                continue
            row_id = ''
            if item_type == 'home':
                row_id = add_page_row('home', label or 'Home', item_type='home', depth=depth, parent_id=parent_id, url_path='/')
            elif item_type in ('page', 'list') and target:
                url_path = f'/{item_path}/'
                row_id = add_page_row(target, label, item_type=item_type, depth=depth, parent_id=parent_id, url_path=url_path)
                if item_type == 'list':
                    dt_tmpl, var_name, slug_field = menu_lib.derive_detail_info(target, tpl_html_dir)
                    if dt_tmpl and var_name:
                        for entry in _dataset_items(data.get(target)):
                            if not isinstance(entry, dict):
                                continue
                            slug = entry.get(slug_field) or entry.get('slug') or entry.get('id')
                            if not slug:
                                continue
                            detail_url_path = f'/{item_path}/{slug}/'
                            detail_row = _seo_row_for_detail(site, lang, target, entry, depth=depth + 1, parent_id=row_id, url_path=detail_url_path)
                            rows.append(detail_row)
            if item.get('children'):
                walk(item.get('children') or [], depth=depth + 1, parent_id=row_id or parent_id, parent_path=child_parent)

    walk(menu_items)

    # 兜底补充渲染任务里出现但菜单树未直接覆盖的页面，通常是兼容旧数据。
    tasks = menu_lib.collect_render_tasks(menu_items, tpl_html_dir, data, pages)
    for task in tasks:
        if task.get('type') in ('home', 'page', 'list'):
            add_page_row(task.get('page_key'), task.get('page_key'), item_type=task.get('type'), depth=0)
    return rows


def _inspect_built_seo_page(site, lang, default_lang, row):
    """Inspect the final generated HTML for checks that source YAML cannot prove."""
    output_root = Path(current_app.config['OUTPUT_DIR']) / str(site.id)
    # output/<site>/index.html 是语言选择页；实际语言页面（包括默认语言）
    # 均优先位于 output/<site>/<lang>/。兼容旧构建结果时才回退根目录。
    localized_root = output_root / lang
    lang_root_path = localized_root if localized_root.exists() else output_root
    url_path = row.get('url_path', '').strip('/')
    if row.get('key') == 'home':
        parts = []
    elif row.get('kind') == 'detail':
        # 优先用 url_path（含菜单父级路径），否则回退到 dataset_key + key
        if url_path:
            parts = url_path.split('/')
        else:
            parts = [row.get('dataset_key'), row.get('key')]
    else:
        if url_path:
            parts = url_path.split('/')
        else:
            parts = [row.get('key')]
    html_path = lang_root_path.joinpath(*(str(p) for p in parts if p), 'index.html')
    result = {
        'built': False, 'path': '/' + '/'.join(str(p) for p in parts if p) + ('/' if parts else ''),
        'h1_count': 0, 'heading_issue': False, 'images_total': 0,
        'images_missing_alt': 0, 'images_empty_alt': 0, 'has_jsonld': False,
        'has_open_graph': False, 'has_twitter_card': False, 'noindex': False,
        'images': [], 'issues': [],
    }
    if not html_path.exists():
        return result
    text = html_path.read_text(encoding='utf-8', errors='replace')
    result['built'] = True
    levels = [int(v) for v in re.findall(r'<h([1-6])\b', text, flags=re.I)]
    result['h1_count'] = levels.count(1)
    result['heading_issue'] = any(b > a + 1 for a, b in zip(levels, levels[1:]))
    images = re.findall(r'<img\b[^>]*>', text, flags=re.I)
    result['images_total'] = len(images)
    result['images_missing_alt'] = sum(1 for tag in images if not re.search(r'\balt\s*=', tag, flags=re.I))
    result['images_empty_alt'] = sum(1 for tag in images if re.search(r'\balt\s*=\s*([\'"])\s*\1', tag, flags=re.I))
    for tag in images[:30]:
        src_match = re.search(r'\bsrc\s*=\s*([\'"])(.*?)\1', tag, flags=re.I | re.S)
        alt_match = re.search(r'\balt\s*=\s*([\'"])(.*?)\1', tag, flags=re.I | re.S)
        src_value = src_match.group(2).strip() if src_match else ''
        alt_value = alt_match.group(2).strip() if alt_match else ''
        result['images'].append({
            'src': (src_value or '(无 src)')[:240],
            'alt': alt_value,
            'alt_state': 'missing' if not alt_match else ('decorative' if not alt_value and not src_value else ('empty' if not alt_value else 'ok')),
        })
    result['has_jsonld'] = bool(re.search(r'type\s*=\s*([\'"])application/ld\+json\1', text, flags=re.I))
    result['has_open_graph'] = bool(re.search(r'property\s*=\s*([\'"])og:', text, flags=re.I))
    result['has_twitter_card'] = bool(re.search(r'name\s*=\s*([\'"])twitter:card\1', text, flags=re.I))
    result['noindex'] = bool(re.search(r'<meta\b[^>]*content\s*=\s*([\'"])[^\'"]*noindex', text, flags=re.I))
    if result['h1_count'] != 1:
        result['issues'].append(f"H1 数量为 {result['h1_count']}")
    if result['heading_issue']:
        result['issues'].append('标题层级存在跳级')
    if result['images_missing_alt']:
        result['issues'].append(f"{result['images_missing_alt']} 张图片缺少 alt")
    if not result['has_open_graph']:
        result['issues'].append('缺少 Open Graph')
    if not result['has_twitter_card']:
        result['issues'].append('缺少 Twitter Card')
    return result


def _seo_health_report(site, lang=None):
    """生成 SEO 健康检查报告。

    这里检查的是店主能理解并能通过现有表单补齐的内容项；技术性 SEO
    文件由构建器自动生成，只检查最近构建输出是否存在。
    """
    default_lang = 'zh-CN'
    meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    if meta_path.exists():
        try:
            meta_data = _yaml.safe_load(meta_path.read_text(encoding='utf-8')) or {}
            default_lang = meta_data.get('default_language') or default_lang
        except Exception:
            default_lang = site.default_language or default_lang
    lang = lang or default_lang
    storage_lang = _storage_lang(site, lang, default_lang)
    settings = read_yaml(site.id, 'settings.yaml') or {}
    company_key = _lang_key('company', site, lang, default_lang)
    company = _merge_settings_section(settings.get('company'), settings.get(company_key))
    tpl_html_dir = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'templates'
    meta = _yaml.safe_load(meta_path.read_text(encoding='utf-8')) if meta_path.exists() else {}

    checks = []

    def add(status, title, detail, action_url='', action_kind='link'):
        checks.append({
            'status': status,
            'title': title,
            'detail': detail,
            'action_url': action_url,
            'action_kind': action_kind,
        })

    if company.get('name'):
        add('ok', '公司名称已填写', '页面标题、OG 站点名和结构化数据会使用公司名称。')
    else:
        add('warn', '缺少公司名称', '公司名称是全站 SEO 的基础字段。', url_for('core.company', site=site.id, lang=lang))

    if company.get('logo'):
        add('ok', 'Logo 已填写', '社交分享图和 Organization 结构化数据有默认图片。')
    else:
        add('warn', '缺少 Logo', '没有页面分享图时会缺少默认 OG 图片。', url_for('core.company', site=site.id, lang=lang))

    if settings.get('slogan') or company.get('slogan') or company.get('description') or company.get('intro'):
        add('ok', '站点简介已填写', '页面 description 缺省时可以回退到站点简介。')
    else:
        add('warn', '缺少站点简介', '建议在公司信息里补一句话简介，作为页面描述兜底。', url_for('core.company', site=site.id, lang=lang))

    pages = {}
    for page_file in list_yaml_files(site.id, 'pages', lang=storage_lang):
        page_key = page_file.stem
        pages[page_key] = read_yaml(site.id, f'pages/{page_file.name}', default={}, lang=storage_lang) or {}

    data = {}
    for data_file in list_yaml_files(site.id, 'data', lang=storage_lang):
        dataset_key = data_file.stem
        data[dataset_key] = read_yaml(site.id, f'data/{data_file.name}', default=[], lang=storage_lang)

    seo_pages = _seo_page_rows(site, lang, settings, pages, data, meta)
    for row in seo_pages:
        # group 是容器节点，无对应页面，跳过页面级检查
        if row.get('kind') == 'group':
            row['inspection'] = {'built': False, 'path': '', 'h1_count': 0, 'heading_issue': False, 'images_total': 0, 'images_missing_alt': 0, 'images_empty_alt': 0, 'has_jsonld': False, 'has_open_graph': False, 'has_twitter_card': False, 'noindex': False, 'images': [], 'issues': []}
            row['health_score'] = 0
            row['ok_count'] = 0
            row['warn_count'] = 0
            row['info_count'] = 0
            row['score_reason'] = ''
            continue
        row['inspection'] = _inspect_built_seo_page(site, lang, default_lang, row)
        inspection = row['inspection']
        if inspection['built']:
            essential_issues = (
                int(inspection['h1_count'] != 1) +
                int(inspection['heading_issue']) +
                int(inspection['images_missing_alt'] > 0)
            )
            row['score'] = max(1, row['score'] - min(2, essential_issues))
        row['score_reason'] = '；'.join(inspection['issues']) if inspection['built'] and inspection['issues'] else '页面内容完整度正常'
        page_ok = 0
        page_warn = 0
        page_info = 0
        title_len = len(_plain_text(row.get('title')))
        description_len = len(_plain_text(row.get('description')))
        if 10 <= title_len <= 60:
            page_ok += 1
        else:
            page_warn += 1
        if 50 <= description_len <= 180:
            page_ok += 1
        elif row.get('description') or row.get('auto_description'):
            page_info += 1
        else:
            page_warn += 1
        if inspection['built']:
            page_ok += int(inspection['h1_count'] == 1)
            page_warn += int(inspection['h1_count'] != 1)
            page_ok += int(not inspection['heading_issue'])
            page_warn += int(inspection['heading_issue'])
            page_ok += int(inspection['images_missing_alt'] == 0)
            page_warn += int(inspection['images_missing_alt'] > 0)
            social_complete = inspection['has_open_graph'] and inspection['has_twitter_card']
            page_ok += int(social_complete)
            page_info += int(not social_complete)
        else:
            page_info += 4
        row['health_score'] = row['score'] * 20
        row['ok_count'] = page_ok
        row['warn_count'] = page_warn
        row['info_count'] = page_info

    # 只检查菜单会实际渲染的页面/详情页，避免把孤立草稿 YAML 当成 SEO 问题。
    menu_items = menu_lib.ensure_home(
        menu_lib.normalize_for_render(
            menu_lib.upgrade_old_format(settings.get('menu') or [], meta.get('datasets', []))
        )
    )
    tasks = menu_lib.collect_render_tasks(menu_items, tpl_html_dir, data, pages)
    checked_pages = set()
    checked_items = set()
    list_pages_without_description = []
    for task in tasks:
        page_key = task.get('page_key')
        task_type = task.get('type')
        if task_type in ('home', 'page', 'list') and page_key and page_key not in checked_pages:
            checked_pages.add(page_key)
            if page_key not in pages:
                continue
            page = pages.get(page_key, {})
            if isinstance(page, dict) and not page.get('description'):
                if task_type == 'list':
                    list_pages_without_description.append(page_key)
                else:
                    add('warn', f'{page_key} 缺少页面简介', '建议补 80-160 字简介，用于 meta description 和分享摘要。',
                        None)

        if task_type == 'detail':
            item = task.get('item') if isinstance(task.get('item'), dict) else {}
            dataset_key = task.get('dataset_key') or ''
            item_key = (dataset_key, item.get('slug') or item.get('id') or item.get('title') or item.get('name'))
            if item_key in checked_items:
                continue
            checked_items.add(item_key)
            item_title = item.get('title') or item.get('name') or item.get('slug') or '未命名条目'
            if not (item.get('summary') or item.get('description') or item.get('excerpt')):
                current_path = task.get('current_path') or ''
                preview_url = ''
                if current_path:
                    preview_url = f"/preview/{site.slug}/{lang}{current_path if current_path.startswith('/') else '/' + current_path}"
                add('warn', f'{dataset_key} / {item_title} 缺少摘要',
                    '详情页 description 和 llms.txt 摘要会变弱，建议补一段简短说明。',
                    url_for('core.dataset_edit', dataset_key=dataset_key, item_id=item.get('id'),
                            _fragment='1', site=site.id, lang=lang, preview_url=preview_url))

    if list_pages_without_description:
        add('info', f'{len(list_pages_without_description)} 个列表页缺少简介',
            '列表页会自动兜底；有时间时可给主要栏目补简介。')

    image_alt_missing = 0
    for task in tasks:
        if task.get('type') != 'detail':
            continue
        item = task.get('item') if isinstance(task.get('item'), dict) else {}
        image_value = item.get('image') or item.get('image_url') or item.get('cover') or item.get('thumbnail')
        has_alt = item.get('alt') or item.get('image_alt') or item.get('imageAlt') or item.get('cover_alt')
        if image_value and not has_alt:
            image_alt_missing += 1
    if image_alt_missing:
        add('info', f'{image_alt_missing} 张详情页图片缺少 alt',
            '可用标题/产品名自动补齐；已有手动 alt 不会被覆盖。',
            url_for('core.seo_repair_alt', site=site.id, lang=lang),
            action_kind='post')

    output_root = Path(current_app.config['OUTPUT_DIR']) / str(site.id)
    missing_output_files = []
    for filename in ('sitemap.xml', 'robots.txt', 'llms.txt'):
        path = output_root / filename
        if path.exists() and path.stat().st_size > 0:
            add('ok', f'{filename} 已生成', '最近一次构建输出中可以找到该文件。')
        else:
            missing_output_files.append(filename)
    if missing_output_files:
        add('warn', 'SEO 附属文件尚未生成', '点击预览、导出或发布后会自动生成 sitemap.xml、robots.txt 和 llms.txt。')
    robots_path = output_root / 'robots.txt'
    if robots_path.exists():
        robots_text = robots_path.read_text(encoding='utf-8', errors='replace')
        if re.search(r'(?im)^\s*Disallow\s*:\s*/\s*$', robots_text):
            add('warn', 'robots.txt 可能屏蔽全站', '发现 Disallow: /，请确认这不是生产站点规则。')
        else:
            add('ok', 'robots.txt 未发现全站屏蔽', '未发现 Disallow: / 规则。')
    built_pages = [row for row in seo_pages if row['inspection'].get('built')]
    noindex_pages = [row['inspection']['path'] for row in built_pages if row['inspection'].get('noindex')]
    if not built_pages:
        add('info', '尚未检查 noindex', '没有可用的页面构建结果，请先预览、导出或发布。')
    elif noindex_pages:
        add('warn', f'{len(noindex_pages)} 个页面包含 noindex', '、'.join(noindex_pages[:8]))
    else:
        add('ok', '页面未发现 noindex', f'已检查 {len(built_pages)} 个生成页面，未检测到 noindex。')

    warn_count = sum(1 for c in checks if c['status'] == 'warn')
    info_count = sum(1 for c in checks if c['status'] == 'info')
    ok_count = sum(1 for c in checks if c['status'] == 'ok')
    score = max(0, 100 - warn_count * 8 - info_count * 2)
    return {
        'score': score,
        'ok_count': ok_count,
        'warn_count': warn_count,
        'info_count': info_count,
        'checks': checks,
        'pages': seo_pages,
        'ai_configured': translation_configured(),
    }


def _alt_from_url(value):
    text = str(value or '').strip()
    if not text:
        return ''
    name = text.rstrip('/').rsplit('/', 1)[-1].split('?', 1)[0].split('#', 1)[0]
    stem = Path(name).stem
    return re.sub(r'[-_]+', ' ', stem).strip()


def _repair_item_image_alt(item):
    """Fill missing image alt values in one dataset item without overriding manual text."""
    if not isinstance(item, dict):
        return 0
    changed = 0
    context = _context_alt(item)

    for field in ('image', 'image_url', 'cover', 'thumbnail', 'photo', 'logo'):
        value = item.get(field)
        if not value:
            continue
        alt_key = _image_alt_key(field)
        if item.get(alt_key) or item.get('alt') or item.get('imageAlt'):
            continue
        item[alt_key] = context or _alt_from_url(value)
        if item.get(alt_key):
            changed += 1

    for list_key in ('images', 'gallery', 'detail_gallery'):
        images = item.get(list_key)
        if not isinstance(images, list):
            continue
        for image in images:
            if not isinstance(image, dict):
                continue
            value = image.get('url') or image.get('image') or image.get('src')
            if value and not image.get('alt'):
                image['alt'] = context or _alt_from_url(value)
                if image.get('alt'):
                    changed += 1

    return changed


def _repair_missing_image_alts(site, lang):
    default_lang = site.default_language or 'zh-CN'
    storage_lang = _storage_lang(site, lang, default_lang)
    total = 0
    touched = []
    for data_file in list_yaml_files(site.id, 'data', lang=storage_lang):
        raw = read_yaml(site.id, f'data/{data_file.name}', default=[], lang=storage_lang)
        items = _dataset_items(raw)
        changed = sum(_repair_item_image_alt(item) for item in items)
        if changed:
            write_yaml(site.id, f'data/{data_file.name}', raw, lang=storage_lang)
            total += changed
            touched.append(data_file.name)
    return total, touched


@bp.route('/seo')
def seo_health():
    user, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    report = _seo_health_report(site, lang=lang)
    if request.args.get('_fragment'):
        return render_template('dashboard/panel_seo.html', user=user, site=site, report=report,
                               current_lang=lang, languages=languages, default_lang=default_lang)
    return render_template('dashboard/seo.html', user=user, site=site, report=report, active='seo',
                           current_lang=lang, languages=languages, default_lang=default_lang)


@bp.route('/seo/workspace')
def seo_workspace():
    user, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    report = _seo_health_report(site, lang=lang)
    return render_template('dashboard/seo_workspace.html', user=user, site=site, report=report,
                           current_lang=lang, languages=languages, default_lang=default_lang)


@bp.route('/seo/repair-alt', methods=['POST'])
def seo_repair_alt():
    """Auto-fill missing image alt text in dataset YAML for the current language."""
    user, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    count, files = _repair_missing_image_alts(site, lang)
    return jsonify({'ok': True, 'count': count, 'files': files})


@bp.route('/seo/page/<path:page_key>', methods=['POST'])
def seo_page_update(page_key):
    """保存单个页面的 SEO 标题/简介，供健康检查工作区使用。"""
    _validate_key(page_key)
    user, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    page = read_yaml(site.id, f'pages/{page_key}.yaml', default={}, lang=storage_lang) or {}
    if not isinstance(page, dict):
        page = {}
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    if title:
        page['title'] = title
    else:
        page.pop('title', None)
    if description:
        page['description'] = description
    else:
        page.pop('description', None)
    write_yaml(site.id, f'pages/{page_key}.yaml', page, lang=storage_lang)
    return jsonify({'ok': True})


@bp.route('/seo/page/<path:page_key>/generate', methods=['POST'])
def seo_page_generate(page_key):
    """从页面现有模块生成简介，返回给弹框填入 textarea。"""
    _validate_key(page_key)
    user, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    page = read_yaml(site.id, f'pages/{page_key}.yaml', default={}, lang=storage_lang) or {}
    settings = read_yaml(site.id, 'settings.yaml') or {}
    company_key = _lang_key('company', site, lang, default_lang)
    company = _merge_settings_section(settings.get('company'), settings.get(company_key))
    company_name = company.get('name') or settings.get('title') or site.name
    page_title = page.get('title') or page_key
    fallback = _auto_page_description(page) or (
        settings.get('slogan') or company.get('slogan') or
        company.get('description') or company.get('intro') or company.get('name') or ''
    )
    page_text = _page_text_for_seo(page) or fallback
    field = request.form.get('field', 'description')
    if field not in ('title', 'description'):
        return jsonify({'ok': False, 'error': '不支持的 SEO 字段'}), 400
    if not translation_configured():
        return jsonify({'ok': False, 'error': 'token 不足'}), 402
    if translation_configured():
        try:
            value = (generate_seo_title(page_title, page_text, company_name=company_name, lang=lang)
                     if field == 'title' else
                     generate_seo_description(page_title, page_text, company_name=company_name, lang=lang))
            payload = {'ok': True, 'field': field, 'value': value, 'source': 'ai'}
            if field == 'description':
                payload['description'] = value  # 兼容旧 SEO 弹窗调用方
            return jsonify(payload)
        except Exception as exc:
            current_app.logger.warning('AI 生成页面 SEO 字段失败: %s', exc)
            return jsonify({'ok': False, 'error': f'AI 生成失败: {exc}'}), 502


def _load_dataset_for_seo(site_id, dataset_key, storage_lang):
    raw = read_yaml(site_id, f'data/{dataset_key}.yaml', default=[], lang=storage_lang)
    if raw is None:
        raw = []
    return raw


def _find_dataset_item(raw, item_key):
    items = _dataset_items(raw)
    item_key = str(item_key)
    for item in items:
        if not isinstance(item, dict):
            continue
        candidates = [item.get('slug'), item.get('id'), item.get('title'), item.get('name')]
        if any(str(value) == item_key for value in candidates if value is not None):
            return item
    return None


@bp.route('/seo/detail/<path:dataset_key>/<path:item_key>', methods=['POST'])
def seo_detail_update(dataset_key, item_key):
    """保存列表详情页的独立 SEO 标题/简介，不覆盖业务标题和正文摘要。"""
    _validate_key(dataset_key)
    _validate_key(item_key)
    user, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    raw = _load_dataset_for_seo(site.id, dataset_key, storage_lang)
    item = _find_dataset_item(raw, item_key)
    if item is None:
        abort(404)
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    if title:
        item['seo_title'] = title
    else:
        item.pop('seo_title', None)
    if description:
        item['seo_description'] = description
    else:
        item.pop('seo_description', None)
    write_yaml(site.id, f'data/{dataset_key}.yaml', raw, lang=storage_lang)
    return jsonify({'ok': True})


@bp.route('/seo/detail/<path:dataset_key>/<path:item_key>/generate', methods=['POST'])
def seo_detail_generate(dataset_key, item_key):
    """从详情页数据生成 SEO 简介。"""
    _validate_key(dataset_key)
    _validate_key(item_key)
    user, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    raw = _load_dataset_for_seo(site.id, dataset_key, storage_lang)
    item = _find_dataset_item(raw, item_key)
    if item is None:
        abort(404)
    settings = read_yaml(site.id, 'settings.yaml') or {}
    company_key = _lang_key('company', site, lang, default_lang)
    company = _merge_settings_section(settings.get('company'), settings.get(company_key))
    company_name = company.get('name') or settings.get('title') or site.name
    page_title = item.get('seo_title') or item.get('title') or item.get('name') or str(item_key)
    fallback = _plain_text(
        item.get('summary') or item.get('description') or item.get('excerpt') or
        item.get('body') or item.get('content') or page_title
    )[:180].rstrip()
    page_text = _detail_item_text_for_seo(item) or fallback
    field = request.form.get('field', 'description')
    if field not in ('title', 'description'):
        return jsonify({'ok': False, 'error': '不支持的 SEO 字段'}), 400
    if not translation_configured():
        return jsonify({'ok': False, 'error': 'token 不足'}), 402
    if translation_configured():
        try:
            value = (generate_seo_title(page_title, page_text, company_name=company_name, lang=lang)
                     if field == 'title' else
                     generate_seo_description(page_title, page_text, company_name=company_name, lang=lang))
            payload = {'ok': True, 'field': field, 'value': value, 'source': 'ai'}
            if field == 'description':
                payload['description'] = value  # 兼容旧 SEO 弹窗调用方
            return jsonify(payload)
        except Exception as exc:
            current_app.logger.warning('AI 生成详情页 SEO 字段失败: %s', exc)
            return jsonify({'ok': False, 'error': f'AI 生成失败: {exc}'}), 502


@bp.route('/company', methods=['GET', 'POST'])
def company():
    user, site = _current_context()
    settings = read_yaml(site.id, 'settings.yaml') or {}

    is_fragment = request.args.get('_fragment') is not None
    lang, languages, default_lang = _get_panel_lang(site)
    company_key = _lang_key('company', site, lang, default_lang)
    contact_key = _lang_key('contact', site, lang, default_lang)

    if request.method == 'POST':
        settings.setdefault('company', {})
        settings.setdefault('contact', {})
        settings.setdefault(company_key, {})
        settings.setdefault(contact_key, {})
        for field in ('name', 'short_name', 'description'):
            settings[company_key][field] = request.form.get(f'company.{field}', '').strip()
        settings['company']['icp'] = request.form.get('company.icp', '').strip()
        if company_key != 'company':
            for field in ('logo', 'favicon', 'icp'):
                settings[company_key].pop(field, None)
        logo_upload = request.files.get('company_logo_file')
        if logo_upload and logo_upload.filename:
            try:
                settings['company']['logo'] = _save_uploaded_image(site.id, logo_upload, prefix='company-logo')
            except Exception as exc:
                flash(f'Logo 上传失败: {exc}')
                if request.form.get('_workspace') == '1':
                    return redirect(url_for('core.company_workspace', site=site.id, lang=lang))
                if is_fragment:
                    return redirect(url_for('core.company', _fragment='1', site=site.id, lang=lang))
                return redirect(url_for('core.company', site=site.id, lang=lang))
        elif 'company.logo' in request.form:
            settings['company']['logo'] = request.form.get('company.logo', '').strip()
        # Favicon 上传（favicon 通常较小，复用图片上传逻辑转 WebP）
        favicon_upload = request.files.get('company_favicon_file')
        if favicon_upload and favicon_upload.filename:
            try:
                settings['company']['favicon'] = _save_uploaded_image(site.id, favicon_upload, prefix='company-favicon')
            except Exception as exc:
                flash(f'Favicon 上传失败: {exc}')
                if request.form.get('_workspace') == '1':
                    return redirect(url_for('core.company_workspace', site=site.id, lang=lang))
                if is_fragment:
                    return redirect(url_for('core.company', _fragment='1', site=site.id, lang=lang))
                return redirect(url_for('core.company', site=site.id, lang=lang))
        elif 'company.favicon' in request.form:
            settings['company']['favicon'] = request.form.get('company.favicon', '').strip()
        # 电话、手机和邮箱属于跨语言联系方式；地址与营业时间允许按站点语言分别维护。
        for field in ('phone', 'mobile', 'email', 'wechat'):
            settings['contact'][field] = request.form.get(f'contact.{field}', '').strip()
        if contact_key != 'contact':
            for field in ('phone', 'email', 'mobile', 'wechat'):
                settings[contact_key].pop(field, None)
        for field in ('address', 'business_hours'):
            settings[contact_key][field] = request.form.get(f'contact.{field}', '').strip()
        admin_settings = settings.setdefault('admin', {})
        admin_settings['auto_save'] = bool(request.form.get('admin.auto_save'))
        write_yaml(site.id, 'settings.yaml', settings)
        flash('已保存')
        if request.form.get('_basic_settings') == '1':
            if request.form.get('_embed') == '1':
                return redirect(url_for('core.basic_settings', embed='1', site=site.id, lang=lang, tab='company'))
            return redirect(url_for('core.basic_settings', _fragment='1', site=site.id, lang=lang, tab='company'))
        if request.form.get('_workspace') == '1':
            return redirect(url_for('core.company_workspace', site=site.id, lang=lang))
        if is_fragment:
            return redirect(url_for('core.company', _fragment='1', site=site.id, lang=lang))
        return redirect(url_for('core.company', site=site.id, lang=lang))

    current_company = _merge_settings_section(settings.get('company'), settings.get(company_key))
    current_contact = _merge_settings_section(settings.get('contact'), settings.get(contact_key))
    source_company = settings.get('company', {})
    source_contact = settings.get('contact', {})

    if is_fragment:
        return render_template('dashboard/panel_company.html',
                               user=user, site=site,
                               company=current_company,
                               contact=current_contact,
                               source_company=source_company,
                               source_contact=source_contact,
                               current_lang=lang,
                               languages=languages,
                               default_lang=default_lang,
                               admin_settings=settings.get('admin') or {})
    return render_template('dashboard/company.html',
                           user=user, site=site,
                           company=current_company,
                           contact=current_contact,
                           source_company=source_company,
                           source_contact=source_contact,
                           current_lang=lang,
                           languages=languages,
                           default_lang=default_lang,
                           admin_settings=settings.get('admin') or {},
                           active='company')


@bp.route('/products')
def products():
    user, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    products = datasets.load(site.id, 'products', lang=storage_lang)
    if request.args.get('_fragment'):
        blocks = _get_available_blocks(site.template_name)
        return render_template('dashboard/panel_data_list.html',
                               user=user, site=site,
                               dataset_key='products', items=products,
                               blocks=blocks,
                               current_lang=lang, languages=languages, default_lang=default_lang)
    return render_template('dashboard/products.html',
                           user=user, site=site, products=products, active='products')


@bp.route('/products/new', methods=['POST'])
def product_new():
    _, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    n = len(datasets.load(site.id, 'products', lang=storage_lang)) + 1
    new_id = datasets.add(site.id, 'products', {
        'name': '新产品', 'slug': f'product-{n}',
        'summary': '', 'description': '', 'cover': '', 'category': '',
        'price': '', 'specs': {},
    }, lang=storage_lang)
    return redirect(url_for('core.product_edit', product_id=new_id, site=site.id, lang=lang))


@bp.route('/products/<int:product_id>/delete', methods=['POST'])
def product_delete(product_id):
    _, site = _current_context()
    lang, _, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    datasets.remove(site.id, 'products', product_id, lang=storage_lang)
    flash('已删除')
    return redirect(url_for('core.products', site=site.id, lang=lang))


@bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
def product_edit(product_id):
    user, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    product = datasets.find(site.id, 'products', product_id, lang=storage_lang)
    if not product:
        abort(404, f'产品不存在: id={product_id}')

    if request.method == 'POST':
        fields = {f: request.form.get(f, '').strip()
                  for f in ('name', 'slug', 'category', 'summary', 'description', 'cover', 'price')}
        fields['cover'] = _uploaded_image_or_form(site.id, 'cover', 'cover_file', 'product-cover')
        # specs: 多行 "键: 值"
        specs = {}
        for line in request.form.get('specs', '').strip().splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                if k.strip():
                    specs[k.strip()] = v.strip()
        fields['specs'] = specs
        datasets.update(site.id, 'products', product_id, fields, lang=storage_lang)
        flash('已保存')
        return redirect(url_for('core.product_edit', product_id=product_id, site=site.id, lang=lang))

    return render_template('dashboard/product_edit.html',
                           user=user, site=site, product=product, active='products')


# ----- 功能 -----

@bp.route('/features')
def features():
    user, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    items = datasets.load(site.id, 'features', lang=storage_lang)
    if request.args.get('_fragment'):
        blocks = _get_available_blocks(site.template_name)
        return render_template('dashboard/panel_data_list.html',
                               user=user, site=site,
                               dataset_key='features', items=items,
                               blocks=blocks,
                               current_lang=lang, languages=languages, default_lang=default_lang)
    return render_template('dashboard/features.html',
                           user=user, site=site, items=items, active='features')


@bp.route('/features/new', methods=['POST'])
def feature_new():
    _, site = _current_context()
    lang, _, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    new_id = datasets.add(site.id, 'features',
                          {'icon': '', 'title': '新功能', 'desc': ''}, lang=storage_lang)
    return redirect(url_for('core.feature_edit', item_id=new_id, site=site.id, lang=lang))


@bp.route('/features/<int:item_id>/delete', methods=['POST'])
def feature_delete(item_id):
    _, site = _current_context()
    lang, _, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    datasets.remove(site.id, 'features', item_id, lang=storage_lang)
    flash('已删除')
    return redirect(url_for('core.features', site=site.id, lang=lang))


@bp.route('/features/<int:item_id>/edit', methods=['GET', 'POST'])
def feature_edit(item_id):
    user, site = _current_context()
    lang, _, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    item = datasets.find(site.id, 'features', item_id, lang=storage_lang)
    if not item:
        abort(404)
    if request.method == 'POST':
        fields = {f: request.form.get(f, '').strip() for f in ('icon', 'title', 'desc')}
        datasets.update(site.id, 'features', item_id, fields, lang=storage_lang)
        flash('已保存')
        return redirect(url_for('core.feature_edit', item_id=item_id, site=site.id, lang=lang))
    return render_template('dashboard/feature_edit.html',
                           user=user, site=site, item=item, active='features')


# ----- 博客 -----

@bp.route('/blog')
def blog():
    user, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    items = datasets.load(site.id, 'posts', lang=storage_lang)
    if request.args.get('_fragment'):
        blocks = _get_available_blocks(site.template_name)
        return render_template('dashboard/panel_data_list.html',
                               user=user, site=site,
                               dataset_key='posts', items=items,
                               blocks=blocks,
                               current_lang=lang, languages=languages, default_lang=default_lang)
    return render_template('dashboard/blog.html',
                           user=user, site=site, items=items, active='blog')


@bp.route('/blog/new', methods=['POST'])
def post_new():
    from datetime import date as _date
    _, site = _current_context()
    lang, _, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    n = len(datasets.load(site.id, 'posts', lang=storage_lang)) + 1
    new_id = datasets.add(site.id, 'posts', {
        'slug': f'post-{n}', 'title': '新文章', 'date': str(_date.today()),
        'cover': '', 'excerpt': '', 'body': '',
    }, lang=storage_lang)
    return redirect(url_for('core.post_edit', item_id=new_id, site=site.id, lang=lang))


@bp.route('/blog/<int:item_id>/delete', methods=['POST'])
def post_delete(item_id):
    _, site = _current_context()
    lang, _, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    datasets.remove(site.id, 'posts', item_id, lang=storage_lang)
    flash('已删除')
    return redirect(url_for('core.blog', site=site.id, lang=lang))


@bp.route('/blog/<int:item_id>/edit', methods=['GET', 'POST'])
def post_edit(item_id):
    user, site = _current_context()
    lang, _, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    item = datasets.find(site.id, 'posts', item_id, lang=storage_lang)
    if not item:
        abort(404)
    if request.method == 'POST':
        fields = {f: request.form.get(f, '').strip()
                  for f in ('title', 'slug', 'date', 'cover', 'excerpt', 'body')}
        fields['cover'] = _uploaded_image_or_form(site.id, 'cover', 'cover_file', 'post-cover')
        datasets.update(site.id, 'posts', item_id, fields, lang=storage_lang)
        flash('已保存')
        return redirect(url_for('core.post_edit', item_id=item_id, site=site.id, lang=lang))
    return render_template('dashboard/post_edit.html',
                           user=user, site=site, item=item, active='blog')


@bp.route('/pages/home', methods=['GET', 'POST'])
def page_home():
    user, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    page = read_yaml(site.id, 'pages/home.yaml', lang=storage_lang) or {}

    # 检测格式: modules 数组 vs 旧固定 key
    is_modules_format = 'modules' in page

    if request.method == 'POST':
        if is_modules_format or request.form.get('_format') == 'modules':
            # modules 数组格式保存
            existing_modules = page.get('modules', [])
            page['modules'] = _parse_modules_form(request.form, existing_modules)
            page.pop('hero', None)
            for k in ('featured_section', 'features_section', 'about_brief', 'blog_section', 'subscribe_section'):
                page.pop(k, None)
        else:
            # 旧固定 key 格式保存
            page.setdefault('hero', {})
            for f in ('title', 'subtitle', 'badge', 'cta_text', 'cta_url', 'video_url', 'background_image'):
                page['hero'][f] = request.form.get(f'hero.{f}', '').strip()
            for key in ('featured_section', 'features_section', 'about_brief', 'blog_section', 'subscribe_section'):
                page.setdefault(key, {})
                page[key]['enabled'] = bool(request.form.get(f'{key}.enabled'))
                for f in ('title', 'subtitle', 'body', 'cta_text', 'cta_url'):
                    v = request.form.get(f'{key}.{f}')
                    if v is not None:
                        page[key][f] = v.strip()
                limit = request.form.get(f'{key}.limit')
                if limit:
                    try:
                        page[key]['limit'] = int(limit)
                    except ValueError:
                        pass
        write_yaml(site.id, 'pages/home.yaml', page, lang=storage_lang)
        flash('已保存')
        if request.args.get('_fragment'):
            return redirect(url_for('core.page_home', _fragment='1', site=site.id, lang=lang))
        return redirect(url_for('core.page_home', site=site.id, lang=lang))

    # 准备渲染上下文
    from .icon_registry import ICON_REGISTRY, icon_names
    from .style_registry import STYLE_REGISTRY
    blocks = _get_available_blocks(site.template_name)
    if is_modules_format:
        page.setdefault('modules', [])
    else:
        page.setdefault('hero', {})
        for key in ('featured_section', 'features_section', 'about_brief', 'blog_section', 'subscribe_section'):
            page.setdefault(key, {})
    # 将 meta.yaml 默认值合并到模块数据，让属性面板显示 CSS 兜底值
    _merge_block_defaults(page.get('modules'), blocks)

    # 收集可用的列表型数据集（供 data-source="" 下拉选择）
    settings_data = read_yaml(site.id, 'settings.yaml') or {}
    tpl_root = Path(current_app.config['TEMPLATES_DIR']) / site.template_name
    meta_data = _yaml.safe_load((tpl_root / 'meta.yaml').read_text(encoding='utf-8')) if (tpl_root / 'meta.yaml').exists() else {}
    raw_menu = settings_data.get('menu', [])
    normalized = menu_lib.ensure_home(menu_lib.normalize_for_render(
        menu_lib.upgrade_old_format(raw_menu, meta_data.get('datasets', []))
    ))
    all_list_datasets = menu_lib.collect_list_targets(normalized)  # #22

    return render_template('dashboard/panel_page_edit.html',
                           user=user, site=site, page=page,
                           page_key='home', page_display_name='首页',
                           is_modules_format=is_modules_format,
                           blocks=blocks,
                           all_list_datasets=all_list_datasets,
                           style_registry=STYLE_REGISTRY,
                           icon_list=icon_names(),
                           icon_registry=ICON_REGISTRY,
                           active='pages_home',
                           current_lang=lang,
                           languages=languages,
                           default_lang=default_lang)


@bp.route('/pages')
def pages():
    return redirect(url_for('core.index'))


def _account_site_or_404(user, site_id):
    """账户中心的站点权限边界；普通用户不能通过篡改 ID 操作他人站点。"""
    site = Site.query.get_or_404(site_id)
    if user.role != 'admin' and site.owner_id != user.id:
        abort(403, '无权操作该站点')
    return site


def _write_audit(user, action, summary, organization_id=None, site_id=None, details=None):
    """追加审计日志；调用方与业务修改在同一事务提交。"""
    db.session.add(AuditLog(
        user_id=user.id if user else None, organization_id=organization_id,
        site_id=site_id, action=action, summary=summary, details=details or {},
        ip_address=(request.headers.get('X-Forwarded-For', request.remote_addr or '').split(',')[0].strip()[:45]),
    ))


def _ensure_personal_organization(user):
    """为旧账户惰性建立个人组织，不批量改动历史站点。"""
    membership = OrganizationMember.query.filter_by(user_id=user.id, role='owner', status='active').first()
    if membership:
        return membership.organization
    # 受邀注册用户只属于受邀组织，不能因打开账户中心而被动获得个人组织和所有者语义。
    if not _user_can_create_sites(user):
        membership = OrganizationMember.query.filter_by(user_id=user.id, status='active').first()
        if membership:
            return membership.organization
        abort(403, '当前账号没有可管理的组织')
    slug = f'account-{user.id}'
    organization = Organization.query.filter_by(slug=slug).first()
    if not organization:
        organization = Organization(name=f'{user.display_name or _public_identifier(user)}的团队', slug=slug, created_by=user.id)
        db.session.add(organization)
        db.session.flush()
    db.session.add(OrganizationMember(organization_id=organization.id, user_id=user.id, role='owner'))
    db.session.commit()
    return organization


def _account_organization_for_user(user, organization_id=None, manage=False):
    if organization_id:
        membership = OrganizationMember.query.filter_by(
            organization_id=organization_id, user_id=user.id, status='active'
        ).first_or_404()
        if manage and membership.role not in {'owner', 'admin'}:
            abort(403)
        return membership.organization, membership
    organization = _ensure_personal_organization(user)
    return organization, OrganizationMember.query.filter_by(
        organization_id=organization.id, user_id=user.id, status='active'
    ).first()


@bp.route('/account')
def account():
    user = _current_user()
    if not user:
        abort(401)

    # 兼容旧的右侧账户面板；新的左下角入口使用完整账户工作区。
    if request.args.get('_fragment'):
        site_query = Site.query.filter(Site.soft_deleted_at.is_(None))
        if user.role != 'admin':
            site_query = site_query.filter_by(owner_id=user.id)
        site = site_query.order_by(Site.id.desc()).first()
        return render_template('dashboard/panel_account.html',
                               user=user, site=site, site_count=site_query.count())

    section = request.args.get('section', 'profile').strip().lower()
    allowed_sections = {'profile', 'sites', 'security', 'organization', 'audit', 'credits', 'integrations', 'billing', 'trash', 'platform'}
    if section not in allowed_sections:
        section = 'profile'
    if section == 'platform' and user.role != 'admin':
        abort(403)
    # 旧链接兼容：建站流程已经从账号中心拆为独立引导页。
    legacy_create_step = request.args.get('create', '').strip().lower() if section == 'sites' else ''
    if legacy_create_step == 'templates':
        return redirect(url_for('core.templates_gallery'))
    if legacy_create_step == 'form':
        return redirect(url_for('core.site_new', template=request.args.get('template', '').strip()))

    site_query = Site.query
    if user.role != 'admin':
        site_query = site_query.filter_by(owner_id=user.id)
    active_sites = site_query.filter(Site.soft_deleted_at.is_(None)).order_by(Site.updated_at.desc()).all()
    deleted_sites = site_query.filter(Site.soft_deleted_at.isnot(None)).order_by(Site.soft_deleted_at.desc()).all()
    editing_site = None
    if section == 'sites' and request.args.get('edit', type=int):
        editing_site = _account_site_or_404(user, request.args.get('edit', type=int))
        if editing_site.soft_deleted_at is not None:
            abort(404)
    account_identity = _identity_for_user(user)
    account_identities = AccountIdentity.query.filter_by(user_id=user.id).order_by(
        AccountIdentity.is_primary.desc(), AccountIdentity.id
    ).all()
    user_sessions = UserSession.query.filter_by(user_id=user.id, revoked_at=None).order_by(
        UserSession.last_seen_at.desc()
    ).all()
    organization, organization_membership = _account_organization_for_user(
        user, request.args.get('org', type=int)
    )
    organizations = OrganizationMember.query.filter_by(user_id=user.id, status='active').all()
    org_members = OrganizationMember.query.filter_by(organization_id=organization.id, status='active').all()
    member_user_ids = [member.user_id for member in org_members]
    org_member_contacts = {
        member_id: {'email': '', 'phone': ''} for member_id in member_user_ids
    }
    org_member_avatars = {
        member.user_id: _account_avatar_url(member.user) for member in org_members
    }
    if member_user_ids:
        identities = AccountIdentity.query.filter(
            AccountIdentity.user_id.in_(member_user_ids),
            AccountIdentity.verified_at.isnot(None),
            AccountIdentity.identity_type.in_(['email', 'phone']),
        ).order_by(AccountIdentity.is_primary.desc(), AccountIdentity.id).all()
        for identity in identities:
            contacts = org_member_contacts[identity.user_id]
            if not contacts[identity.identity_type]:
                contacts[identity.identity_type] = identity.identifier
        # 兼容尚未迁移到 AccountIdentity 的旧邮箱账户。
        for member in org_members:
            contacts = org_member_contacts[member.user_id]
            legacy_email = (member.user.email or '').strip()
            if not contacts['email'] and legacy_email and not legacy_email.endswith('@identity.invalid'):
                contacts['email'] = legacy_email
    org_site_ids = [row.site_id for row in OrganizationSite.query.filter_by(organization_id=organization.id).all()]
    org_shared_sites = Site.query.filter(
        Site.id.in_(org_site_ids), Site.soft_deleted_at.is_(None)
    ).order_by(Site.updated_at.desc()).all() if org_site_ids else []
    pending_invitations = OrganizationInvitation.query.filter_by(
        organization_id=organization.id, status='pending'
    ).filter(OrganizationInvitation.expires_at > datetime.now(timezone.utc)).order_by(
        OrganizationInvitation.created_at.desc()
    ).all()
    organization_invite_url = session.pop('organization_invite_url', None)
    audit_filters = {
        'q': request.args.get('q', '').strip()[:100],
        'category': request.args.get('category', '').strip().lower()[:30],
        'date_from': request.args.get('date_from', '').strip()[:10],
        'date_to': request.args.get('date_to', '').strip()[:10],
    }
    audit_query = AuditLog.query.filter_by(user_id=user.id)
    category_prefixes = {
        'account': ('account.',),
        'security': ('security.', 'wechat.'),
        'site': ('site.',),
        'organization': ('organization.',),
        'billing': ('billing.',),
    }
    prefixes = category_prefixes.get(audit_filters['category'])
    if prefixes:
        audit_query = audit_query.filter(or_(*[AuditLog.action.startswith(prefix) for prefix in prefixes]))
    if audit_filters['q']:
        keyword = f"%{audit_filters['q']}%"
        audit_query = audit_query.filter(or_(
            AuditLog.summary.ilike(keyword), AuditLog.action.ilike(keyword),
            AuditLog.ip_address.ilike(keyword),
        ))
    try:
        if audit_filters['date_from']:
            audit_query = audit_query.filter(
                AuditLog.created_at >= datetime.fromisoformat(audit_filters['date_from']).replace(tzinfo=timezone.utc)
            )
        if audit_filters['date_to']:
            audit_query = audit_query.filter(
                AuditLog.created_at < (datetime.fromisoformat(audit_filters['date_to']) + timedelta(days=1)).replace(tzinfo=timezone.utc)
            )
    except ValueError:
        audit_filters['date_from'] = ''
        audit_filters['date_to'] = ''
    audit_page = audit_query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).paginate(
        page=max(request.args.get('page', 1, type=int), 1), per_page=20, error_out=False
    )
    audit_logs = audit_page.items
    credit_account = AiCreditAccount.query.filter_by(user_id=user.id).first()
    if not credit_account:
        credit_account = AiCreditAccount(user_id=user.id, balance=100)
        db.session.add(credit_account)
        db.session.flush()
        db.session.add(AiCreditTransaction(account_id=credit_account.id, amount=100, balance_after=100,
                                           source='welcome', description='新账户体验额度'))
        db.session.commit()
    credit_transactions = AiCreditTransaction.query.filter_by(account_id=credit_account.id).order_by(AiCreditTransaction.id.desc()).limit(50).all()
    totp = TotpCredential.query.filter_by(user_id=user.id).first()
    wechat_identity = ExternalIdentity.query.filter_by(user_id=user.id, provider='wechat').first()
    plans = BillingPlan.query.filter_by(is_active=True).order_by(BillingPlan.price_cents).all()
    if not plans:
        db.session.add_all([
            BillingPlan(code='free', name='基础版', price_cents=0, billing_period='year'),
            BillingPlan(code='pro-placeholder', name='专业版（待定价）', price_cents=0, billing_period='year'),
        ])
        db.session.commit()
        plans = BillingPlan.query.filter_by(is_active=True).order_by(BillingPlan.id).all()
    subscription = Subscription.query.filter_by(user_id=user.id).order_by(Subscription.id.desc()).first()
    orders = BillingOrder.query.filter_by(user_id=user.id).order_by(BillingOrder.id.desc()).limit(20).all()
    platform_users = []
    if user.role == 'admin':
        for platform_user in User.query.order_by(User.id).all():
            identity = AccountIdentity.query.filter_by(user_id=platform_user.id, is_primary=True).first()
            platform_users.append({
                'id': platform_user.id,
                'identifier': identity.identifier if identity else platform_user.email,
                'display_name': platform_user.display_name or '未设置昵称',
                'role': platform_user.role,
                'status': platform_user.status,
                'site_count': Site.query.filter_by(owner_id=platform_user.id).count(),
                'created_at': platform_user.created_at,
                'last_login_at': platform_user.last_login_at,
                'is_current': platform_user.id == user.id,
            })
    accessible_site_query = Site.query.filter(Site.soft_deleted_at.is_(None))
    if user.role != 'admin':
        shared_site_ids = db.session.query(OrganizationSite.site_id).join(
            OrganizationMember, OrganizationMember.organization_id == OrganizationSite.organization_id
        ).filter(OrganizationMember.user_id == user.id, OrganizationMember.status == 'active')
        accessible_site_query = accessible_site_query.filter(or_(
            Site.owner_id == user.id, Site.id.in_(shared_site_ids)
        ))
    account_return_site = accessible_site_query.order_by(Site.updated_at.desc()).first()
    account_return_url = (url_for('core.overview', site=account_return_site.id)
                          if account_return_site else url_for('core.templates_gallery'))
    site_create_step = request.args.get('create', '').strip().lower() if section == 'sites' else ''
    site_templates = []
    selected_site_template = None
    selected_template_languages = []
    if site_create_step in {'templates', 'form'} and _user_can_create_sites(user):
        scan_templates()
        site_templates = _visible_templates_query().all()
        selected_name = request.args.get('template', '').strip()
        if site_create_step == 'form':
            selected_site_template = next((item for item in site_templates if item.name == selected_name), None)
            if not selected_site_template:
                return redirect(url_for('core.account', section='sites', create='templates'))
            meta_path = Path(current_app.config['TEMPLATES_DIR']) / selected_site_template.name / 'meta.yaml'
            meta = _yaml.safe_load(meta_path.read_text(encoding='utf-8')) or {} if meta_path.exists() else {}
            selected_template_languages = meta.get('languages') or [{'code': 'zh-CN', 'name': '简体中文'}]
    return render_template('dashboard/account_workspace.html',
                           user=user, section=section, active_sites=active_sites,
                           deleted_sites=deleted_sites, editing_site=editing_site,
                           account_identity=account_identity,
                           account_identities=account_identities,
                           account_identifier=_public_identifier(user), user_sessions=user_sessions,
                           current_session_hash=_hash_token(session.get('auth_session_token', '')) if session.get('auth_session_token') else '',
                           pending_identity=session.get('pending_account_identity'), organization=organization,
                           organization_membership=organization_membership, organizations=organizations,
                           org_members=org_members, org_member_contacts=org_member_contacts,
                           org_member_avatars=org_member_avatars,
                           org_site_ids=org_site_ids,
                           pending_invitations=pending_invitations,
                           organization_invite_url=organization_invite_url,
                           org_shared_sites=org_shared_sites,
                           site_create_step=site_create_step, site_templates=site_templates,
                           selected_site_template=selected_site_template,
                           selected_template_languages=selected_template_languages,
                           can_create_sites=_user_can_create_sites(user), audit_logs=audit_logs,
                           audit_page=audit_page, audit_filters=audit_filters,
                           credit_account=credit_account, credit_transactions=credit_transactions,
                           totp=totp, wechat_identity=wechat_identity, plans=plans,
                           subscription=subscription, orders=orders,
                           platform_users=platform_users,
                           account_return_url=account_return_url)


@bp.route('/account/profile', methods=['POST'])
def account_profile_save():
    """保存平台级个人资料；邮箱身份由认证流程维护，不在普通资料表单中修改。"""
    user = _current_user()
    if not user:
        abort(401)
    display_name = request.form.get('display_name', '').strip()
    if len(display_name) > 80:
        flash('昵称不能超过 80 个字符', 'danger')
        return redirect(url_for('core.account', section='profile'))
    avatar = request.files.get('avatar')
    avatar_updated = False
    if avatar and avatar.filename:
        if request.content_length and request.content_length > 6 * 1024 * 1024:
            flash('头像文件不能超过 5MB', 'danger')
            return redirect(url_for('core.account', section='profile'))
        try:
            from PIL import Image, ImageOps, UnidentifiedImageError
            from PIL.Image import DecompressionBombError
            Image.MAX_IMAGE_PIXELS = 25_000_000
            image = Image.open(avatar.stream)
            if image.format not in {'JPEG', 'PNG', 'WEBP', 'GIF'}:
                raise ValueError('头像仅支持 JPG、PNG、WebP 或 GIF 图片')
            image.seek(0)
            image = ImageOps.exif_transpose(image).convert('RGB')
            image = ImageOps.fit(image, (512, 512), method=Image.Resampling.LANCZOS)
            avatar_path = _account_avatar_path(user.id)
            avatar_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = avatar_path.with_suffix('.tmp.webp')
            image.save(temp_path, 'WEBP', quality=88, method=6)
            temp_path.replace(avatar_path)
            avatar_updated = True
        except (UnidentifiedImageError, DecompressionBombError, OSError, ValueError) as exc:
            current_app.logger.warning('用户 %s 上传头像失败: %s', user.id, exc)
            flash(str(exc) if isinstance(exc, ValueError) else '头像文件无效或已损坏', 'danger')
            return redirect(url_for('core.account', section='profile'))
    user.display_name = display_name or None
    _write_audit(user, 'account.profile.update', '更新个人资料和头像' if avatar_updated else '更新个人资料',
                 details={'avatar_updated': avatar_updated})
    db.session.commit()
    flash('个人资料已保存', 'success')
    return redirect(url_for('core.account', section='profile',
                            workspace_changed='1' if avatar_updated else None))


@bp.route('/account/avatar/<int:user_id>.webp')
def account_avatar(user_id):
    if not _current_user():
        abort(401)
    avatar_path = _account_avatar_path(user_id)
    if not avatar_path.is_file():
        abort(404)
    response = send_from_directory(avatar_path.parent, avatar_path.name, mimetype='image/webp')
    response.cache_control.public = False
    response.cache_control.max_age = 3600
    return response


@bp.route('/account/sites/<int:site_id>/identity', methods=['POST'])
def account_site_identity_update(site_id):
    """修改后台站点名称和 Slug；访客可见品牌信息仍由网站设置管理。"""
    from .models import SLUG_RESERVED

    user = _current_user()
    if not user:
        abort(401)
    site = _account_site_or_404(user, site_id)
    if site.soft_deleted_at is not None:
        abort(404)

    name = request.form.get('name', '').strip()
    slug = request.form.get('slug', '').strip().lower()
    old_name, old_slug = site.name, site.slug
    redirect_edit = lambda: redirect(url_for('core.account', section='sites', edit=site.id))

    if not name or len(name) > 200:
        flash('站点名称不能为空且不能超过 200 个字符', 'danger')
        return redirect_edit()
    if not SLUG_PATTERN.match(slug):
        flash('Slug 需为 3–30 位小写字母、数字或连字符，且不能以连字符开头或结尾', 'danger')
        return redirect_edit()
    if slug in SLUG_RESERVED:
        flash('该 Slug 为系统保留字，请更换', 'danger')
        return redirect_edit()

    slug_changed = slug != old_slug
    occupied_site = Site.query.filter(Site.slug == slug, Site.id != site.id).first()
    occupied_alias = SiteSlugAlias.query.filter_by(slug=slug).first()
    if occupied_site or (occupied_alias and occupied_alias.site_id != site.id):
        flash('该 Slug 已被其他站点或历史地址使用', 'danger')
        return redirect_edit()
    if slug_changed and site.status == 'published' and request.form.get('slug_change_confirmed') != '1':
        flash('已发布站点修改 Slug 需要再次确认', 'warning')
        return redirect_edit()

    site.name = name
    if slug_changed:
        if occupied_alias and occupied_alias.site_id == site.id:
            db.session.delete(occupied_alias)
        if not SiteSlugAlias.query.filter_by(slug=old_slug).first():
            db.session.add(SiteSlugAlias(site_id=site.id, slug=old_slug))
        site.slug = slug
    _write_audit(
        user, 'site.identity.update', f'更新站点“{old_name}”的名称或 Slug', site_id=site.id,
        details={'old_name': old_name, 'new_name': name, 'old_slug': old_slug, 'new_slug': slug},
    )
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash('Slug 刚被其他站点占用，请换一个', 'danger')
        return redirect_edit()
    flash('站点信息已保存' + ('；旧 Slug 会继续转到当前站点' if slug_changed else ''), 'success')
    return redirect(url_for('core.account', section='sites', workspace_changed='1'))


@bp.route('/account/sites/<int:site_id>/trash', methods=['POST'])
def account_site_trash(site_id):
    """将站点移入回收站，只改状态，不删除任何用户文件。"""
    user = _current_user()
    if not user:
        abort(401)
    site = _account_site_or_404(user, site_id)
    if site.soft_deleted_at is None:
        site.soft_deleted_at = datetime.now(timezone.utc)
        _write_audit(user, 'site.trash', f'将站点“{site.name}”移入回收站', site_id=site.id)
        db.session.commit()
    if session.get('current_site_id') == site.id:
        session.pop('current_site_id', None)
    flash(f'站点“{site.name}”已移入回收站', 'success')
    return redirect(url_for('core.account', section='sites', workspace_changed='1'))


@bp.route('/account/sites/<int:site_id>/restore', methods=['POST'])
def account_site_restore(site_id):
    """恢复软删除站点，数据库记录和磁盘文件保持原位。"""
    user = _current_user()
    if not user:
        abort(401)
    site = _account_site_or_404(user, site_id)
    site.soft_deleted_at = None
    _write_audit(user, 'site.restore', f'恢复站点“{site.name}”', site_id=site.id)
    db.session.commit()
    flash(f'站点“{site.name}”已恢复', 'success')
    return redirect(url_for('core.account', section='trash', workspace_changed='1'))


@bp.route('/account/sessions/<int:session_id>/revoke', methods=['POST'])
def account_session_revoke(session_id):
    """撤销本人的指定设备会话，禁止通过 ID 操作其他用户。"""
    user = _current_user()
    if not user:
        abort(401)
    login_session = UserSession.query.filter_by(id=session_id, user_id=user.id).first_or_404()
    login_session.revoked_at = datetime.now(timezone.utc)
    _write_audit(user, 'security.session.revoke', '撤销登录设备', details={'session_id': session_id})
    db.session.commit()
    if session.get('auth_session_token') and login_session.token_hash == _hash_token(session['auth_session_token']):
        session.clear()
        flash('当前设备已退出登录', 'success')
        return redirect(url_for('core.login'))
    flash('设备会话已退出', 'success')
    return redirect(url_for('core.account', section='security'))


@bp.route('/account/identities/request', methods=['POST'])
def account_identity_request():
    """为已登录用户绑定新的邮箱或手机号，验证前不写入身份表。"""
    user = _current_user()
    if not user:
        abort(401)
    identity_type, identifier = _normalize_identity(request.form.get('identifier'))
    if not identifier:
        flash('请输入有效的邮箱或手机号', 'danger')
    elif AccountIdentity.query.filter_by(identifier=identifier).first():
        flash('该邮箱或手机号已被其他账号使用', 'danger')
    elif _login_rate_limited(f'bind:{user.id}:{identifier}'):
        flash('验证码请求过于频繁，请稍后再试', 'danger')
    else:
        try:
            dev_code = _create_verification_code(identity_type, identifier, 'bind_identity', {'user_id': user.id})
        except RuntimeError as exc:
            flash(str(exc), 'danger')
        else:
            session['pending_account_identity'] = {
                'type': identity_type, 'identifier': identifier, 'dev_code': dev_code,
            }
            flash('验证码已发送，请完成验证', 'success')
    return redirect(url_for('core.account', section='security'))


@bp.route('/account/identities/verify', methods=['POST'])
def account_identity_verify():
    user = _current_user()
    if not user:
        abort(401)
    pending = session.get('pending_account_identity') or {}
    identifier = pending.get('identifier')
    record = _consume_verification_code(identifier, 'bind_identity', request.form.get('code')) if identifier else None
    if not record or (record.payload or {}).get('user_id') != user.id:
        flash('验证码错误、已过期或尝试次数过多', 'danger')
    elif AccountIdentity.query.filter_by(identifier=identifier).first():
        flash('该身份已经被绑定', 'warning')
    else:
        db.session.add(AccountIdentity(
            user_id=user.id, identity_type=pending['type'], identifier=identifier,
            verified_at=datetime.now(timezone.utc), is_primary=not bool(user.identities),
        ))
        _write_audit(user, 'security.identity.bind', f'绑定{pending["type"]}身份 {identifier}')
        db.session.commit()
        session.pop('pending_account_identity', None)
        flash('新账号标识已绑定', 'success')
    return redirect(url_for('core.account', section='security'))


@bp.route('/account/identities/<int:identity_id>/primary', methods=['POST'])
def account_identity_primary(identity_id):
    user = _current_user()
    if not user:
        abort(401)
    identity = AccountIdentity.query.filter_by(id=identity_id, user_id=user.id).first_or_404()
    AccountIdentity.query.filter_by(user_id=user.id).update({'is_primary': False})
    identity.is_primary = True
    _write_audit(user, 'security.identity.primary', f'设置主登录身份 {identity.identifier}')
    db.session.commit()
    flash('主登录账号已更新', 'success')
    return redirect(url_for('core.account', section='security'))


@bp.route('/account/identities/<int:identity_id>/delete', methods=['POST'])
def account_identity_delete(identity_id):
    user = _current_user()
    if not user:
        abort(401)
    identity = AccountIdentity.query.filter_by(id=identity_id, user_id=user.id).first_or_404()
    if identity.is_primary or AccountIdentity.query.filter_by(user_id=user.id).count() <= 1:
        flash('主账号或唯一账号不能解绑', 'danger')
    else:
        _write_audit(user, 'security.identity.unbind', f'解绑身份 {identity.identifier}')
        db.session.delete(identity)
        db.session.commit()
        flash('账号标识已解绑', 'success')
    return redirect(url_for('core.account', section='security'))


@bp.route('/account/organization', methods=['POST'])
def account_organization_save():
    user = _current_user()
    organization, actor = _account_organization_for_user(user, request.form.get('organization_id', type=int), manage=True)
    name = request.form.get('name', '').strip()
    if not name or len(name) > 120:
        flash('团队名称不能为空且不能超过 120 个字符', 'danger')
    else:
        organization.name = name
        _write_audit(user, 'organization.update', f'修改团队名称为“{name}”', organization_id=organization.id)
        db.session.commit()
        flash('团队资料已保存', 'success')
    return redirect(url_for('core.account', section='organization'))


@bp.route('/account/organization/members', methods=['POST'])
def account_organization_member_add():
    user = _current_user()
    organization, actor = _account_organization_for_user(user, request.form.get('organization_id', type=int), manage=True)
    identity_type, identifier = _normalize_identity(request.form.get('identifier'))
    role = request.form.get('role', 'viewer')
    if role not in {'admin', 'editor', 'viewer'}:
        abort(400)
    identity = AccountIdentity.query.filter_by(identifier=identifier).first() if identifier else None
    if not identifier:
        flash('请输入有效的邮箱或手机号', 'danger')
    elif identity and identity.user_id == user.id:
        flash('不能邀请自己加入当前团队', 'warning')
    elif identity and OrganizationMember.query.filter_by(organization_id=organization.id, user_id=identity.user_id).first():
        flash('该用户已经是团队成员', 'warning')
    else:
        OrganizationInvitation.query.filter_by(
            organization_id=organization.id, identifier=identifier, status='pending'
        ).update({'status': 'revoked'})
        raw_token = secrets.token_urlsafe(32)
        invitation = OrganizationInvitation(
            organization_id=organization.id, identity_type=identity_type,
            identifier=identifier, role=role, token_hash=_hash_token(raw_token),
            invited_by=user.id, expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        db.session.add(invitation)
        db.session.flush()
        _write_audit(user, 'organization.invitation.create', f'邀请成员 {identifier}',
                     organization_id=organization.id,
                     details={'role': role, 'invitation_id': invitation.id})
        db.session.commit()
        session['organization_invite_url'] = url_for(
            'core.organization_invitation_accept', token=raw_token, _external=True
        )
        flash('团队邀请已创建，7 天内有效', 'success')
    return redirect(url_for('core.account', section='organization', org=organization.id))


@bp.route('/account/organization/invitations/<int:invitation_id>/revoke', methods=['POST'])
def account_organization_invitation_revoke(invitation_id):
    user = _current_user()
    invitation = OrganizationInvitation.query.get_or_404(invitation_id)
    organization, actor = _account_organization_for_user(user, invitation.organization_id, manage=True)
    if invitation.status != 'pending':
        flash('该邀请已不能撤销', 'warning')
    else:
        invitation.status = 'revoked'
        _write_audit(user, 'organization.invitation.revoke', f'撤销成员邀请 {invitation.identifier}',
                     organization_id=organization.id, details={'invitation_id': invitation.id})
        db.session.commit()
        flash('团队邀请已撤销', 'success')
    return redirect(url_for('core.account', section='organization', org=organization.id))


@bp.route('/account/organization/members/<int:member_id>', methods=['POST'])
def account_organization_member_update(member_id):
    user = _current_user()
    member = OrganizationMember.query.get_or_404(member_id)
    organization, actor = _account_organization_for_user(user, member.organization_id, manage=True)
    if member.role == 'owner':
        flash('组织所有者不能在此删除或降级', 'danger')
        return redirect(url_for('core.account', section='organization', org=organization.id))
    action = request.form.get('action')
    if action == 'remove':
        _write_audit(user, 'organization.member.remove', f'移除成员 {member.user_id}', organization_id=organization.id)
        db.session.delete(member)
        flash('成员已移除', 'success')
    else:
        role = request.form.get('role')
        if role not in {'admin', 'editor', 'viewer'}:
            abort(400)
        member.role = role
        _write_audit(user, 'organization.member.role', f'调整成员 {member.user_id} 的角色', organization_id=organization.id,
                     details={'role': role})
        flash('成员角色已更新', 'success')
    db.session.commit()
    return redirect(url_for('core.account', section='organization', org=organization.id))


@bp.route('/account/organization/sites/<int:site_id>', methods=['POST'])
def account_organization_site_toggle(site_id):
    user = _current_user()
    organization, actor = _account_organization_for_user(user, request.form.get('organization_id', type=int), manage=True)
    site = _account_site_or_404(user, site_id)
    link = OrganizationSite.query.filter_by(organization_id=organization.id, site_id=site.id).first()
    if link:
        db.session.delete(link)
        action, summary = 'organization.site.remove', f'取消关联站点“{site.name}”'
    else:
        db.session.add(OrganizationSite(organization_id=organization.id, site_id=site.id))
        action, summary = 'organization.site.add', f'关联站点“{site.name}”'
    _write_audit(user, action, summary, organization_id=organization.id, site_id=site.id)
    db.session.commit()
    return redirect(url_for('core.account', section='organization'))


@bp.route('/account/integrations/wechat/mock', methods=['POST'])
def account_wechat_mock():
    """开发环境模拟微信绑定；生产环境必须走开放平台 OAuth。"""
    user = _current_user()
    if not (current_app.debug or current_app.testing):
        abort(403, '生产环境禁止模拟微信绑定')
    identity = ExternalIdentity.query.filter_by(user_id=user.id, provider='wechat').first()
    if not identity:
        identity = ExternalIdentity(user_id=user.id, provider='wechat',
                                    provider_user_id=f'mock-{user.id}', nickname='微信开发模拟', is_mock=True)
        db.session.add(identity)
        _write_audit(user, 'wechat.bind.mock', '绑定微信开发模拟身份')
        db.session.commit()
    flash('已绑定微信开发模拟身份；这不是真实微信授权', 'warning')
    return redirect(url_for('core.account', section='integrations'))


@bp.route('/account/integrations/wechat/unbind', methods=['POST'])
def account_wechat_unbind():
    user = _current_user()
    identity = ExternalIdentity.query.filter_by(user_id=user.id, provider='wechat').first()
    if identity:
        db.session.delete(identity)
        _write_audit(user, 'wechat.unbind', '解绑微信身份')
        db.session.commit()
    flash('微信身份已解绑', 'success')
    return redirect(url_for('core.account', section='integrations'))


@bp.route('/account/billing/orders', methods=['POST'])
def account_billing_order_create():
    """创建待支付订单；未接支付渠道时绝不改变为已支付。"""
    user = _current_user()
    plan = BillingPlan.query.filter_by(id=request.form.get('plan_id', type=int), is_active=True).first_or_404()
    order = BillingOrder(user_id=user.id, plan_id=plan.id, amount_cents=plan.price_cents,
                         status='pending', provider='placeholder')
    db.session.add(order)
    _write_audit(user, 'billing.order.create', f'创建套餐“{plan.name}”待支付订单')
    db.session.commit()
    flash('已创建待支付订单；支付渠道尚未接入，未发生真实扣款', 'warning')
    return redirect(url_for('core.account', section='billing'))


@bp.route('/sites/delete', methods=['POST'])
def site_delete():
    """兼容旧入口：改为可恢复的软删除，禁止直接清除用户站点文件。"""
    user, site = _current_context()
    if user.role != 'admin' and site.owner_id != user.id:
        abort(403)
    site_name = site.name
    site.soft_deleted_at = datetime.now(timezone.utc)
    db.session.commit()
    session.pop('current_site_id', None)
    flash(f'站点“{site_name}”已移入回收站', 'success')
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.args.get('_fragment'):
        return jsonify({'ok': True, 'redirect': url_for('core.overview')})
    return redirect(url_for('core.overview'))
def _save_link_list(site_id, settings_key):
    """收集表单 label[] 和 url[], 写回 settings.yaml[settings_key]."""
    settings = read_yaml(site_id, 'settings.yaml') or {}
    labels = request.form.getlist('label[]')
    urls = request.form.getlist('url[]')
    items = []
    for label, url in zip(labels, urls):
        label, url = label.strip(), url.strip()
        if label or url:
            items.append({'label': label, 'url': url})
    settings[settings_key] = items
    write_yaml(site_id, 'settings.yaml', settings)


@bp.route('/settings/header', methods=['GET', 'POST'])
def header_edit():
    """网站头部变体选择 + 语言切换按钮配置."""
    user, site = _current_context()
    settings = read_yaml(site.id, 'settings.yaml') or {}
    is_fragment = request.args.get('_fragment') is not None
    lang, languages, default_lang = _get_panel_lang(site)

    # Header 变体列表（模板 meta 中定义）
    tpl_meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    tpl_meta = _yaml.safe_load(tpl_meta_path.read_text(encoding='utf-8')) if tpl_meta_path.exists() else {}
    header_variants = tpl_meta.get('header_variants', [
        {'key': 'logo_left_menu_right', 'label': 'Logo 左 + 菜单右', 'description': '经典布局，适合大多数企业网站'},
        {'key': 'logo_center_menu_below', 'label': 'Logo 居中 + 菜单下方', 'description': '对称布局，适合品牌展示'},
        {'key': 'minimal_hamburger', 'label': '极简（汉堡菜单）', 'description': 'Logo 左 + 汉堡菜单，移动端友好'},
    ])

    # 模板定义的全部语言
    template_languages = tpl_meta.get('languages', [
        {'code': 'zh-CN', 'name': '简体中文', 'flag': '🇨🇳'},
        {'code': 'zh-TW', 'name': '繁體中文', 'flag': '🇹🇼'},
        {'code': 'en', 'name': 'English', 'flag': '🇺🇸'},
    ])
    # 当前启用的语言列表以 Site 模型为准，避免 settings.header.enabled_languages 旧缓存污染面板显示
    all_template_codes = [l['code'] for l in template_languages]
    enabled_languages = [c for c in (site.enabled_languages or all_template_codes) if c in all_template_codes]
    # 复选框展示模板全部语言（不按 enabled 过滤），让管理员能看到并勾选新增的语言版本
    visible_template_languages = list(template_languages)

    # 语言切换按钮样式列表
    lang_switcher_styles = [
        {'key': 'inline_row', 'label': '水平行内（中文 | EN | JP）'},
        {'key': 'vertical_dropdown', 'label': '垂直下拉'},
        {'key': 'flag_icon', 'label': '旗帜 + 简称'},
    ]

    if request.method == 'POST':
        header = settings.setdefault('header', {})
        header['variant'] = request.form.get('header_variant', header_variants[0]['key'])
        header['language_switcher'] = {
            'enabled': bool(request.form.get('lang_switcher_enabled')),
            'style': request.form.get('lang_switcher_style', 'vertical_dropdown'),
        }
        # 保存启用的语言版本（多选）
        selected_langs = request.form.getlist('enabled_lang')
        all_codes = [l['code'] for l in template_languages]
        if selected_langs:
            # 只保留模板中存在的语言代码
            header['enabled_languages'] = [c for c in selected_langs if c in all_codes]
        else:
            # 至少保留默认语言
            default_lang = tpl_meta.get('default_language', all_codes[0] if all_codes else 'zh-CN')
            header['enabled_languages'] = [default_lang]
        # 同步到 Site 模型
        site.enabled_languages = header['enabled_languages']
        from .db import db
        db.session.commit()
        write_yaml(site.id, 'settings.yaml', settings)
        flash('已保存')
        current_lang = request.args.get('lang')
        redirect_args = {'site': site.id}
        if current_lang:
            redirect_args['lang'] = current_lang
        if is_fragment:
            return redirect(url_for('core.header_edit', _fragment='1', **redirect_args))
        return redirect(url_for('core.header_edit', **redirect_args))

    current_header = settings.get('header') or {}
    header_variant_keys = [v['key'] for v in header_variants]
    if current_header.get('variant') not in header_variant_keys:
        current_header = dict(current_header)
        current_header['variant'] = header_variant_keys[0] if header_variant_keys else 'logo_left_menu_right'
    # 显示仍以 Site.enabled_languages 为准；保存时会同步 settings.header.enabled_languages
    enabled_languages = [c for c in (site.enabled_languages or all_template_codes) if c in all_template_codes]
    # 复选框展示模板全部语言（不按 enabled 过滤），让管理员能看到并勾选新增的语言版本
    visible_template_languages = list(template_languages)
    if is_fragment:
        return render_template('dashboard/panel_header.html',
                               user=user, site=site,
                               header_variants=header_variants,
                               template_languages=visible_template_languages,
                               enabled_languages=enabled_languages,
                               lang_switcher_styles=lang_switcher_styles,
                               current_header=current_header,
                               settings=settings)
    return render_template('dashboard/header_edit.html',
                           user=user, site=site,
                           header_variants=header_variants,
                           template_languages=visible_template_languages,
                           enabled_languages=enabled_languages,
                           lang_switcher_styles=lang_switcher_styles,
                           current_header=current_header,
                           active='header')


def _footer_link_choices(settings, template_meta):
    """Flatten configured navigation into selectable footer link targets."""
    raw_menu = menu_lib.upgrade_old_format(
        settings.get('menu') or template_meta.get('default_menu', []),
        template_meta.get('datasets', []),
    )
    normalized = menu_lib.normalize_for_render(raw_menu)
    choices = []
    seen = set()

    def walk(items, depth=0):
        for item in items or []:
            if not isinstance(item, dict):
                continue
            url = str(item.get('url') or '').strip()
            if url and url != '#' and item.get('type') != 'group':
                if url.startswith('/') and url != '/' and '?' not in url and '#' not in url and not url.endswith('/'):
                    url += '/'
                if url not in seen:
                    choices.append({'label': f"{'— ' * depth}{item.get('label') or url}", 'url': url})
                    seen.add(url)
            walk(item.get('children') or [], depth + 1)

    walk(normalized)
    return choices


@bp.route('/settings/footer_variant', methods=['GET', 'POST'])
def footer_variant_edit():
    """网站底部变体选择."""
    user, site = _current_context()
    settings = read_yaml(site.id, 'settings.yaml') or {}
    is_fragment = request.args.get('_fragment') is not None
    lang, languages, default_lang = _get_panel_lang(site)
    footer_key = _lang_key('footer', site, lang, default_lang)

    # Footer 变体列表
    tpl_meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    tpl_meta = _yaml.safe_load(tpl_meta_path.read_text(encoding='utf-8')) if tpl_meta_path.exists() else {}
    footer_link_choices = _footer_link_choices(settings, tpl_meta)
    footer_variants = tpl_meta.get('footer_variants', [
        {'key': 'columns', 'label': '栏目模式', 'description': '多列链接和文本栏目'},
        {'key': 'minimal', 'label': '极简模式', 'description': '仅显示版权和备案信息'},
        {'key': 'columns_social', 'label': '栏目 + 社交', 'description': '左侧公司 Logo 和社交图标，右侧栏目'},
    ])

    if request.method == 'POST':
        footer = settings.setdefault(footer_key, {})
        footer['variant'] = request.form.get('footer_variant', 'columns')
        if request.form.get('_use_company_meta'):
            footer.pop('copyright', None)
            footer.pop('icp', None)
        else:
            footer['copyright'] = request.form.get('copyright', '').strip()
            footer['icp'] = request.form.get('icp', '').strip()

        if any(k == 'social_enabled' or k.startswith('social_') for k in request.form):
            social = settings.setdefault('social', {})
            social['enabled'] = bool(request.form.get('social_enabled'))
            for platform in ('github', 'twitter', 'facebook', 'instagram', 'linkedin', 'youtube',
                             'tiktok', 'whatsapp', 'telegram', 'wechat', 'weibo',
                             'xiaohongshu', 'pinterest', 'discord'):
                social[platform] = request.form.get(f'social_{platform}', '').strip()

        # 解析底部栏目
        col_count = 0
        try:
            col_count = int(request.form.get('footer_column_count', '0'))
        except (ValueError, TypeError):
            pass
        columns = []
        for ci in range(col_count):
            col = {
                'type': request.form.get(f'footer_col_{ci}_type', 'menu').strip(),
                'title': request.form.get(f'footer_col_{ci}_title', '').strip(),
            }
            if col['type'] not in ('menu', 'text'):
                col['type'] = 'menu'
            if col['type'] == 'text':
                col['text'] = request.form.get(f'footer_col_{ci}_text', '').strip()
            link_count = 0
            try:
                link_count = int(request.form.get(f'footer_col_{ci}_link_count', '0'))
            except (ValueError, TypeError):
                pass
            links = []
            for li in range(link_count):
                label = request.form.get(f'footer_col_{ci}_link_{li}_label', '').strip()
                url = request.form.get(f'footer_col_{ci}_link_{li}_url', '').strip()
                if label or url:
                    links.append({'label': label, 'url': url})
            col['links'] = links
            columns.append(col)
        if columns:
            footer['columns'] = columns
        else:
            footer.pop('columns', None)

        write_yaml(site.id, 'settings.yaml', settings)
        flash('已保存')
        if is_fragment:
            return redirect(url_for('core.footer_variant_edit', _fragment='1', site=site.id, lang=lang))
        return redirect(url_for('core.footer_variant_edit', site=site.id, lang=lang))

    current_footer = settings.get(footer_key) or settings.get('footer') or {}
    source_footer = settings.get('footer') or {}
    footer_variant_keys = [v['key'] for v in footer_variants]
    if current_footer.get('variant') not in footer_variant_keys:
        current_footer = dict(current_footer)
        current_footer['variant'] = footer_variant_keys[0] if footer_variant_keys else 'columns'

    if is_fragment:
        return render_template('dashboard/panel_footer_variant.html',
                               user=user, site=site,
                               footer_variants=footer_variants,
                               current_footer=current_footer,
                               source_footer=source_footer,
                               settings=settings,
                               current_lang=lang,
                               languages=languages,
                               default_lang=default_lang,
                               footer_link_choices=footer_link_choices)
    return render_template('dashboard/footer_variant.html',
                           user=user, site=site,
                           footer_variants=footer_variants,
                           current_footer=current_footer,
                           source_footer=source_footer,
                           settings=settings,
                           current_lang=lang,
                           languages=languages,
                           default_lang=default_lang,
                           footer_link_choices=footer_link_choices,
                           active='footer_variant')


@bp.route('/settings/header_footer', methods=['GET', 'POST'])
def header_footer_edit():
    """Combined header/footer editor for the center workspace."""
    user, site = _current_context()
    settings = read_yaml(site.id, 'settings.yaml') or {}
    lang, languages, default_lang = _get_panel_lang(site)
    tab = request.args.get('tab') or request.form.get('_header_footer_tab') or 'header'
    if tab not in ('header', 'footer'):
        tab = 'header'

    tpl_meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    tpl_meta = _yaml.safe_load(tpl_meta_path.read_text(encoding='utf-8')) if tpl_meta_path.exists() else {}

    header_variants = tpl_meta.get('header_variants', [
        {'key': 'logo_left_menu_right', 'label': 'Logo 左 + 菜单右', 'description': '经典布局，适合大多数企业网站'},
        {'key': 'logo_center_menu_below', 'label': 'Logo 居中 + 菜单下方', 'description': '对称布局，适合品牌展示'},
        {'key': 'minimal_hamburger', 'label': '极简（汉堡菜单）', 'description': 'Logo 左 + 汉堡菜单，移动端友好'},
    ])
    template_languages = tpl_meta.get('languages', [
        {'code': 'zh-CN', 'name': '简体中文', 'flag': '🇨🇳'},
        {'code': 'zh-TW', 'name': '繁體中文', 'flag': '🇹🇼'},
        {'code': 'en', 'name': 'English', 'flag': '🇺🇸'},
    ])
    all_template_codes = [l['code'] for l in template_languages]

    footer_variants = tpl_meta.get('footer_variants', [
        {'key': 'columns', 'label': '栏目模式', 'description': '多列链接和文本栏目'},
        {'key': 'minimal', 'label': '极简模式', 'description': '仅显示版权和备案信息'},
        {'key': 'columns_social', 'label': '栏目 + 社交', 'description': '左侧公司 Logo 和社交图标，右侧栏目'},
    ])
    footer_key = _lang_key('footer', site, lang, default_lang)
    footer_link_choices = _footer_link_choices(settings, tpl_meta)

    if request.method == 'POST':
        section = request.form.get('_section') or tab
        if section == 'header':
            header = settings.setdefault('header', {})
            header['variant'] = request.form.get('header_variant', header_variants[0]['key'])
            header['language_switcher'] = {
                'enabled': bool(request.form.get('lang_switcher_enabled')),
                'style': request.form.get('lang_switcher_style', 'vertical_dropdown'),
            }
            selected_langs = request.form.getlist('enabled_lang')
            if selected_langs:
                header['enabled_languages'] = [c for c in selected_langs if c in all_template_codes]
            else:
                default_header_lang = tpl_meta.get('default_language', all_template_codes[0] if all_template_codes else 'zh-CN')
                header['enabled_languages'] = [default_header_lang]
            site.enabled_languages = header['enabled_languages']
            from .db import db
            db.session.commit()
            tab = 'header'
        else:
            footer = settings.setdefault(footer_key, {})
            footer['variant'] = request.form.get('footer_variant', 'columns')
            if request.form.get('_use_company_meta'):
                footer.pop('copyright', None)
                footer.pop('icp', None)
            else:
                footer['copyright'] = request.form.get('copyright', '').strip()
                footer['icp'] = request.form.get('icp', '').strip()

            if any(k == 'social_enabled' or k.startswith('social_') for k in request.form):
                social = settings.setdefault('social', {})
                social['enabled'] = bool(request.form.get('social_enabled'))
                for platform in ('github', 'twitter', 'facebook', 'instagram', 'linkedin', 'youtube',
                                 'tiktok', 'whatsapp', 'telegram', 'wechat', 'weibo',
                                 'xiaohongshu', 'pinterest', 'discord'):
                    social[platform] = request.form.get(f'social_{platform}', '').strip()

            try:
                col_count = int(request.form.get('footer_column_count', '0'))
            except (ValueError, TypeError):
                col_count = 0
            columns = []
            for ci in range(col_count):
                col = {
                    'type': request.form.get(f'footer_col_{ci}_type', 'menu').strip(),
                    'title': request.form.get(f'footer_col_{ci}_title', '').strip(),
                }
                if col['type'] not in ('menu', 'text'):
                    col['type'] = 'menu'
                if col['type'] == 'text':
                    col['text'] = request.form.get(f'footer_col_{ci}_text', '').strip()
                try:
                    link_count = int(request.form.get(f'footer_col_{ci}_link_count', '0'))
                except (ValueError, TypeError):
                    link_count = 0
                links = []
                for li in range(link_count):
                    label = request.form.get(f'footer_col_{ci}_link_{li}_label', '').strip()
                    url = request.form.get(f'footer_col_{ci}_link_{li}_url', '').strip()
                    if label or url:
                        links.append({'label': label, 'url': url})
                col['links'] = links
                columns.append(col)
            if columns:
                footer['columns'] = columns
            else:
                footer.pop('columns', None)
            tab = 'footer'

        write_yaml(site.id, 'settings.yaml', settings)
        flash('已保存')
        return redirect(url_for('core.header_footer_edit', embed='1', site=site.id, lang=lang, tab=tab, saved='1'))

    current_header = settings.get('header') or {}
    header_variant_keys = [v['key'] for v in header_variants]
    if current_header.get('variant') not in header_variant_keys:
        current_header = dict(current_header)
        current_header['variant'] = header_variant_keys[0] if header_variant_keys else 'logo_left_menu_right'
    enabled_languages = [c for c in (site.enabled_languages or all_template_codes) if c in all_template_codes]
    lang_switcher_styles = [
        {'key': 'inline_row', 'label': '水平行内（中文 | EN | JP）'},
        {'key': 'vertical_dropdown', 'label': '垂直下拉'},
        {'key': 'flag_icon', 'label': '旗帜 + 简称'},
    ]

    current_footer = settings.get(footer_key) or settings.get('footer') or {}
    source_footer = settings.get('footer') or {}
    footer_variant_keys = [v['key'] for v in footer_variants]
    if current_footer.get('variant') not in footer_variant_keys:
        current_footer = dict(current_footer)
        current_footer['variant'] = footer_variant_keys[0] if footer_variant_keys else 'columns'

    header_form_action = url_for('core.header_footer_edit', embed='1', site=site.id, lang=lang, tab='header')
    footer_form_action = url_for('core.header_footer_edit', embed='1', site=site.id, lang=lang, tab='footer')

    return render_template('dashboard/settings_workspace.html',
                           title='页头页脚',
                           panel_template='dashboard/panel_header_footer.html',
                           user=user, site=site, active='header_footer',
                           header_variants=header_variants,
                           template_languages=list(template_languages),
                           enabled_languages=enabled_languages,
                           lang_switcher_styles=lang_switcher_styles,
                           current_header=current_header,
                           footer_variants=footer_variants,
                           current_footer=current_footer,
                           source_footer=source_footer,
                           settings=settings,
                           current_lang=lang,
                           languages=languages,
                           default_lang=default_lang,
                           header_footer_tab=tab,
                           header_form_action=header_form_action,
                           footer_form_action=footer_form_action,
                           footer_link_choices=footer_link_choices,
                           settings_workspace=True)


def _ensure_menu_item_ids(items):
    """Add stable IDs used to distinguish saved menu items from newly added ones."""
    changed = False
    used = set()

    def walk(nodes):
        nonlocal changed
        for item in nodes or []:
            if not isinstance(item, dict):
                continue
            item_id = str(item.get('id') or '').strip()
            if not re.fullmatch(r'[a-z0-9]{8,32}', item_id) or item_id in used:
                item_id = secrets.token_hex(6)
                while item_id in used:
                    item_id = secrets.token_hex(6)
                item['id'] = item_id
                changed = True
            used.add(item_id)
            walk(item.get('children') or [])

    walk(items)
    return changed


def _lock_saved_menu_types(existing_items, submitted_items):
    """Server-side enforcement for menu types that were already persisted."""
    saved_items = {}

    def index(nodes):
        for item in nodes or []:
            if not isinstance(item, dict):
                continue
            item_id = str(item.get('id') or '')
            if item_id:
                saved_items[item_id] = item
            index(item.get('children') or [])

    def apply(nodes):
        for item in nodes or []:
            if not isinstance(item, dict):
                continue
            item_id = str(item.get('id') or '')
            old = saved_items.get(item_id)
            if old:
                old_type = old.get('type') or 'link'
                item['type'] = old_type
                if old_type in {'list', 'page', 'group'}:
                    item.pop('url', None)
                    if not item.get('target') and old.get('target'):
                        item['target'] = old['target']
                elif old_type == 'link':
                    item.pop('target', None)
                    if not item.get('url') and old.get('url'):
                        item['url'] = old['url']
                else:
                    item.pop('target', None)
                    item.pop('url', None)
            apply(item.get('children') or [])

    index(existing_items)
    apply(submitted_items)


@bp.route('/settings/menu', methods=['GET', 'POST'])
def menu_edit():
    user, site = _current_context()
    settings = read_yaml(site.id, 'settings.yaml') or {}
    is_fragment = request.args.get('_fragment') is not None
    is_embed = request.args.get('embed') == '1'

    lang, languages, default_lang = _get_panel_lang(site)

    # ── 自动迁移: 把旧 menu_<lang> 转为 menu_labels ──
    menu_labels = settings.get('menu_labels') or {}
    migrated = False
    for lopt in (languages or []):
        code = lopt['code']
        old_key = f'menu_{code}'
        if old_key in settings and settings[old_key]:
            old_menu = settings[old_key]
            old_labels = menu_lib.extract_labels(old_menu)
            if old_labels:
                menu_labels[code] = old_labels
            del settings[old_key]
            migrated = True
    # 兜底: 只对默认语言用当前 menu 标签初始化 menu_labels，避免把简体中文
    # 错误复制到繁体中文等非默认语言（_language_label_map 已做 fallback 合并）
    if migrated or not menu_labels:
        fallback_labels = menu_lib.extract_labels(settings.get('menu', []))
        if fallback_labels:
            if default_lang not in menu_labels or not menu_labels[default_lang]:
                menu_labels[default_lang] = dict(fallback_labels)
            migrated = True
    if migrated:
        settings['menu_labels'] = menu_labels

    if request.method == 'POST':
        existing_menu = copy.deepcopy(settings.get('menu') or [])
        _ensure_menu_item_ids(existing_menu)
        menu_json = request.form.get('menu_json', '').strip()
        if menu_json:
            try:
                raw_items = _yaml.safe_load(menu_json) or []
            except _yaml.YAMLError:
                raw_items = []
            items = menu_lib.clean_for_storage(raw_items)
        else:
            # 旧表单兼容分支（一般不会走到了）
            labels = request.form.getlist('label[]')
            raw_items = [{'label': '首页', 'type': 'home'}]
            types = request.form.getlist('type[]')
            targets_list = request.form.getlist('target_list[]')
            urls_link = request.form.getlist('url_link[]')
            children_values = request.form.getlist('children_json[]')
            for i, label in enumerate(labels):
                label = label.strip()
                if not label:
                    continue
                t = types[i] if i < len(types) else 'link'
                raw = {'label': label, 'type': t}
                if t in ('list', 'page'):
                    target = targets_list[i].strip() if i < len(targets_list) else ''
                    if target:
                        raw['target'] = target
                elif t == 'link':
                    url = urls_link[i].strip() if i < len(urls_link) else ''
                    if url:
                        raw['url'] = url
                children_raw = children_values[i].strip() if i < len(children_values) else ''
                if children_raw:
                    try:
                        children = _yaml.safe_load(children_raw) or []
                    except _yaml.YAMLError:
                        children = []
                    if isinstance(children, list):
                        raw['children'] = children
                raw_items.append(raw)
            items = menu_lib.clean_for_storage(raw_items)

        _lock_saved_menu_types(existing_menu, items)
        _ensure_menu_item_ids(items)

        # 保存：结构写入 menu，标签写入 menu_labels.<lang>
        # 默认语言直接覆盖 menu；非默认语言用 merge_structure 保留已有标签
        if lang == default_lang:
            settings['menu'] = items
        else:
            settings['menu'] = menu_lib.merge_structure(settings.get('menu', []), items)
        labels = menu_lib.extract_labels(items)
        if labels:
            menu_labels = settings.get('menu_labels') or {}
            menu_labels[lang] = labels
            settings['menu_labels'] = menu_labels
        write_yaml(site.id, 'settings.yaml', settings)
        if lang == default_lang:
            _ensure_detail_templates_for_menu(site.id, items)
        flash('已保存，首页已保持为固定入口')
        if is_embed:
            return redirect(url_for('core.menu_edit', embed='1', site=site.id, lang=lang, saved='1'))
        if is_fragment:
            return redirect(url_for('core.menu_edit', _fragment='1', site=site.id, lang=lang))
        return redirect(url_for('core.menu_edit', site=site.id, lang=lang))

    # GET: 加载菜单 —— 共享结构 + 当前语言标签覆盖
    meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    meta = _yaml.safe_load(meta_path.read_text(encoding='utf-8')) if meta_path.exists() else {}
    raw_menu = settings.get('menu') or meta.get('default_menu', [])
    if _ensure_menu_item_ids(raw_menu):
        settings['menu'] = raw_menu
        write_yaml(site.id, 'settings.yaml', settings)
    items = menu_lib.ensure_home(
        menu_lib.upgrade_old_format(raw_menu, meta.get('datasets', []))
    )
    # 所有语言：用 menu_labels 覆盖标签（让用户看到当前语言的翻译）
    labels = (settings.get('menu_labels') or {}).get(lang, {})
    if labels:
        items = menu_lib.apply_labels(items, labels)

    # 默认语言菜单（AI 翻译原文来源）
    default_menu_raw = settings.get('menu') or meta.get('default_menu', [])
    source_menu = menu_lib.ensure_home(
        menu_lib.upgrade_old_format(default_menu_raw, meta.get('datasets', []))
    )

    if is_fragment:
        return render_template('dashboard/panel_menu.html',
                               user=user, site=site, items=items,
                               source_menu=source_menu,
                               current_lang=lang, languages=languages, default_lang=default_lang)
    if is_embed:
        return render_template('dashboard/settings_workspace.html',
                               title='菜单配置',
                               panel_template='dashboard/panel_menu.html',
                               user=user, site=site, items=items, active='menu',
                               source_menu=source_menu,
                               current_lang=lang, languages=languages, default_lang=default_lang,
                               menu_form_action=url_for('core.menu_edit', embed='1', site=site.id, lang=lang),
                               settings_workspace=True)
    return render_template('dashboard/menu.html',
                           user=user, site=site, items=items, active='menu',
                           source_menu=source_menu,
                           current_lang=lang, languages=languages, default_lang=default_lang)


@bp.route('/settings/footer', methods=['GET', 'POST'])
def footer_edit():
    """旧页脚链接页面 —— 已迁移至 footer_variant_edit，自动转换旧数据格式"""
    user, site = _current_context()
    settings = read_yaml(site.id, 'settings.yaml') or {}

    # 迁移旧的 footer_links 数据到新 footer.columns 格式
    old_links = settings.pop('footer_links', None)
    if old_links:
        footer = settings.setdefault('footer', {})
        existing_cols = footer.get('columns', [])
        if not existing_cols:
            footer['variant'] = 'columns'
            footer['columns'] = [{
                'type': 'menu',
                'title': '快速链接',
                'links': old_links
            }]
            write_yaml(site.id, 'settings.yaml', settings)
            flash('页脚链接数据已自动迁移到新版格式')

    return redirect(url_for('core.footer_variant_edit', site=site.id))


@bp.route('/settings/social', methods=['GET', 'POST'])
def social_edit():
    user, site = _current_context()
    settings = read_yaml(site.id, 'settings.yaml') or {}
    is_fragment = request.args.get('_fragment') is not None
    if request.method == 'POST':
        social = settings.setdefault('social', {})
        for platform in ('github', 'twitter', 'facebook', 'instagram', 'linkedin', 'youtube',
                         'tiktok', 'whatsapp', 'telegram', 'wechat', 'weibo',
                         'xiaohongshu', 'pinterest', 'discord'):
            social[platform] = request.form.get(platform, '').strip()
        write_yaml(site.id, 'settings.yaml', settings)
        flash('已保存')
        if is_fragment:
            return redirect(url_for('core.social_edit', _fragment='1', site=site.id))
        return redirect(url_for('core.social_edit', site=site.id))
    social = settings.get('social') or {}
    if is_fragment:
        return render_template('dashboard/panel_social.html',
                               user=user, site=site, social=social)
    return render_template('dashboard/social.html',
                           user=user, site=site, social=social, active='social')


@bp.route('/settings/theme', methods=['GET', 'POST'])
def theme_edit():
    user, site = _current_context()
    settings = read_yaml(site.id, 'settings.yaml') or {}
    is_fragment = request.args.get('_fragment') is not None
    tpl_meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    tpl_meta = _yaml.safe_load(tpl_meta_path.read_text(encoding='utf-8')) if tpl_meta_path.exists() else {}
    default_theme = tpl_meta.get('default_theme') or {}

    if request.method == 'POST':
        # 颜色值会被 _base.html 用 |safe 注入 <style> 块（关闭转义），
        # 必须在入库前按白名单校验，否则 `red}</style><script>...` 可闭合标签注入脚本。
        # 复用 block_renderer 的同一套颜色白名单，保持全项目一致。
        from .block_renderer import _SAFE_COLOR
        theme = settings.setdefault('theme', {})
        for key in ('color-primary', 'color-bg', 'color-surface', 'color-text', 'color-text-secondary', 'color-border'):
            v = request.form.get(key, '').strip()
            if v and _SAFE_COLOR.match(v):
                theme[key] = v
            else:
                # 空值或非法颜色一律清除该键，回退到模板默认色
                theme.pop(key, None)
        font_family = request.form.get('font-family-base', '').strip()
        allowed_fonts = {
            'system': "-apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif",
            'yahei': "'Microsoft YaHei', 'PingFang SC', 'Noto Sans SC', sans-serif",
            'serif': "Georgia, 'Times New Roman', 'Songti SC', serif",
        }
        if font_family in allowed_fonts:
            theme['font-family-base'] = allowed_fonts[font_family]
            theme['font-sans'] = allowed_fonts[font_family]
        font_size = request.form.get('font-size-base', '').strip()
        if re.fullmatch(r'(?:1[2-9]|2[0-2])px', font_size):
            theme['font-size-base'] = font_size
            theme['text-body-md'] = font_size
        # 清理旧版短 key（迁移前遗留数据）
        for old_key in ('accent', 'bg', 'surface', 'text', 'text_muted', 'border'):
            theme.pop(old_key, None)
        write_yaml(site.id, 'settings.yaml', settings)
        flash('已保存')
        if request.form.get('_basic_settings') == '1':
            lang, _, default_lang = _get_panel_lang(site)
            if request.form.get('_embed') == '1':
                return redirect(url_for('core.basic_settings', embed='1', site=site.id, lang=lang, tab='theme'))
            return redirect(url_for('core.basic_settings', _fragment='1', site=site.id, lang=lang, tab='theme'))
        if request.form.get('_workspace') == '1':
            return redirect(url_for('core.theme_workspace', site=site.id))
        if is_fragment:
            return redirect(url_for('core.theme_edit', _fragment='1', site=site.id))
        return redirect(url_for('core.theme_edit', site=site.id))

    theme = settings.get('theme') or {}
    font_value = theme.get('font-family-base', '')
    font_choice = 'serif' if 'Georgia' in font_value else ('yahei' if 'Microsoft YaHei' in font_value else 'system')
    font_size_value = theme.get('font-size-base', '16px')
    if is_fragment:
        return render_template('dashboard/panel_theme.html',
                               user=user, site=site, theme=theme, default_theme=default_theme,
                               font_choice=font_choice, font_size_value=font_size_value)
    return render_template('dashboard/theme.html',
                           user=user, site=site, theme=theme, default_theme=default_theme, active='theme',
                           font_choice=font_choice, font_size_value=font_size_value)


SLUG_PATTERN = re.compile(r'^[a-z0-9][a-z0-9-]{1,28}[a-z0-9]$')

# page_key / dataset_key 经 <path:> 转换器接收, 会原样带进 `..` 和 `/`。
# 这里做路由层白名单, 与 site_storage._safe_path 的存储层兜底形成双保险。
# 字符集放宽到下划线 + 允许单字符, 覆盖现有所有 key(about/contact/home/
# portfolio/posts/pricing/products/features), 零误伤。
_KEY_PATTERN = re.compile(r'^[a-z0-9][a-z0-9_-]{0,40}$')
VISIBLE_TEMPLATE_NAMES = ('claude', 'dengtec')


def _visible_templates_query():
    return Template.query.filter(Template.name.in_(VISIBLE_TEMPLATE_NAMES)).order_by(Template.name)


def _validate_key(key):
    """校验动态 page_key / dataset_key, 非法直接 404(不暴露细节)."""
    if not _KEY_PATTERN.match(key or ''):
        abort(404)
    return key


@bp.route('/templates')
def templates_gallery():
    # 新注册用户尚无站点时也必须能进入模板库创建第一个站点。
    user = _current_user()
    if not user:
        abort(401)
    query = Site.query.filter(Site.soft_deleted_at.is_(None))
    if user.role != 'admin':
        query = query.filter_by(owner_id=user.id)
    site = query.order_by(Site.id.desc()).first()
    scan_templates()
    templates = _visible_templates_query().all()
    if request.args.get('_fragment'):
        return render_template('dashboard/panel_templates.html',
                               user=user, site=site, templates=templates,
                               can_create_sites=_user_can_create_sites(user))
    return render_template('dashboard/templates_gallery.html', user=user, site=site,
                           templates=templates, can_create_sites=_user_can_create_sites(user),
                           has_sites=bool(site))


@bp.route('/templates/<template_name>/preview/')
@bp.route('/templates/<template_name>/preview/<path:filepath>')
def template_preview(template_name, filepath='index.html'):
    """模板预览 —— 用模板 seed_data 渲染."""
    session['current_template_preview'] = template_name  # 后续 /assets/ 请求需要定位资源目录
    if template_name not in VISIBLE_TEMPLATE_NAMES or not Template.query.filter_by(name=template_name).first():
        abort(404)
    out = build_template_preview(
        template_name,
        base_url=f'/templates/{template_name}/preview',
    )
    full = out / filepath
    if full.is_dir():
        full = full / 'index.html'
        filepath = f'{filepath.rstrip("/")}/index.html'
    return _safe_send_from_directory(out, filepath)


@bp.route('/api/sites/slug-available')
def site_slug_available():
    """Validate a site slug while the create-site form is being filled in."""
    from .models import SLUG_RESERVED
    slug = request.args.get('slug', '').strip().lower()
    if not SLUG_PATTERN.match(slug):
        return jsonify({'valid': False, 'available': False,
                        'message': '请输入 3–30 位小写字母、数字或连字符'})
    if slug in SLUG_RESERVED:
        return jsonify({'valid': True, 'available': False, 'message': '该 Slug 为系统保留字'})
    available = not Site.query.filter_by(slug=slug).first() and not SiteSlugAlias.query.filter_by(slug=slug).first()
    return jsonify({'valid': True, 'available': available,
                    'message': '该 Slug 可以使用' if available else '该 Slug 已被占用'})


@bp.route('/sites/new', methods=['GET', 'POST'])
def site_new():
    from .models import SLUG_RESERVED
    template_name = request.args.get('template')
    template = _visible_templates_query().filter_by(name=template_name).first() if template_name else None
    templates = _visible_templates_query().all()

    def template_language_options(tpl_name):
        meta_path = Path(current_app.config['TEMPLATES_DIR']) / tpl_name / 'meta.yaml'
        if not meta_path.exists():
            return [{'code': 'zh-CN', 'name': '简体中文'}], 'zh-CN'
        meta = _yaml.safe_load(meta_path.read_text(encoding='utf-8')) or {}
        languages = meta.get('languages') or [{'code': 'zh-CN', 'name': '简体中文'}]
        default_lang = meta.get('default_language') or (languages[0].get('code') if languages else 'zh-CN')
        return languages, default_lang

    template_language_map = {}
    template_default_language_map = {}
    for tpl in templates:
        langs, default_lang = template_language_options(tpl.name)
        template_language_map[tpl.name] = langs
        template_default_language_map[tpl.name] = default_lang

    user = _current_user()
    if not user:
        return redirect(url_for('core.login'))
    if not _user_can_create_sites(user):
        abort(403, '受邀成员账号没有创建个人站点的权限')

    is_fragment = request.args.get('_fragment') is not None

    initial_template_name = template.name if template else (templates[0].name if templates else '')
    initial_default_lang = template_default_language_map.get(initial_template_name, 'zh-CN')
    form = {
        'name': '',
        'slug': '',
        'template_name': template.name if template else '',
        'enabled_languages': [initial_default_lang],
    }
    error = None

    if request.method == 'POST':
        form['name'] = request.form.get('name', '').strip()
        form['slug'] = request.form.get('slug', '').strip().lower()
        form['template_name'] = request.form.get('template_name', '').strip()
        form['enabled_languages'] = request.form.getlist('enabled_lang')

        # 解析模板：未选时使用第一个可用模板
        selected_template = _visible_templates_query().filter_by(name=form['template_name']).first()
        if not selected_template:
            selected_template = _visible_templates_query().first()
        selected_languages, selected_default_lang = (
            template_language_options(selected_template.name) if selected_template else ([], 'zh-CN')
        )
        selected_codes = [l.get('code') for l in selected_languages if l.get('code')]
        selected_enabled_langs = [c for c in form.get('enabled_languages', []) if c in selected_codes]
        if not selected_template:
            error = '暂无可用模板，请联系管理员'
        elif not form['name']:
            error = '请填写站点名'
        elif not SLUG_PATTERN.match(form['slug']):
            error = 'Slug 不合法（要求 3–30 字符，[a-z 0-9 -]，不以 - 开头/结尾）'
        elif form['slug'] in SLUG_RESERVED:
            error = f'Slug "{form["slug"]}" 是保留字'
        elif Site.query.filter_by(slug=form['slug']).first() or SiteSlugAlias.query.filter_by(slug=form['slug']).first():
            error = f'Slug "{form["slug"]}" 已被占用'
        else:
            if not selected_enabled_langs:
                error = '请选择至少一种模板支持的语言版本'
                if is_fragment:
                    return jsonify({'ok': False, 'error': error})
                current_site = Site.query.filter_by(owner_id=user.id).order_by(Site.id.desc()).first()
                return render_template('dashboard/site_new.html',
                                       user=user,
                                       site=current_site,
                                       template=template, templates=templates, form=form, error=error,
                                       template_language_map=template_language_map,
                                       template_default_language_map=template_default_language_map,
                                       active='templates')
            else:
                from .db import db
                default_language = selected_default_lang if selected_default_lang in selected_enabled_langs else selected_enabled_langs[0]
                site = Site(
                    owner_id=user.id, name=form['name'], slug=form['slug'],
                    folder_path='', template_name=selected_template.name,
                    template_version=selected_template.current_version, cdn_provider='aliyun',
                    default_language=default_language,
                    enabled_languages=selected_enabled_langs,
                )
                from sqlalchemy.exc import IntegrityError
                db.session.add(site)
                # #12+#29: flush(触发 INSERT, slug 唯一约束在此生效) 和文件初始化都纳入保护。
                # 上面虽已查过 slug 唯一性, 但 查→insert 之间存在 TOCTOU(并发建同名 slug),
                # 唯一约束会抛 IntegrityError; 文件操作也可能失败。两种都回滚 DB + 友好提示, 不 500。
                try:
                    db.session.flush()  # 拿到 site.id, 但先不 commit
                    site.folder_path = f'sites/{site.id}'
                    init_site_folder(site.id)
                    copy_seed_data(site.id, selected_template.name)
                    settings = read_yaml(site.id, 'settings.yaml') or {}
                    header = settings.setdefault('header', {})
                    header['enabled_languages'] = selected_enabled_langs
                    header.setdefault('language_switcher', {})['enabled'] = len(selected_enabled_langs) > 1
                    write_yaml(site.id, 'settings.yaml', settings)
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()
                    error = f'Slug "{form["slug"]}" 刚被占用，请换一个'
                    if is_fragment:
                        return jsonify({'ok': False, 'error': error})
                    current_site = Site.query.filter_by(owner_id=user.id).order_by(Site.id.desc()).first()
                    return render_template('dashboard/site_new.html',
                                           user=user, site=current_site,
                                           template=template, templates=templates, form=form, error=error,
                                           template_language_map=template_language_map,
                                           template_default_language_map=template_default_language_map,
                                           active='templates')
                except Exception:
                    db.session.rollback()
                    current_app.logger.exception('建站文件初始化失败, 已回滚 DB (slug=%s)', form['slug'])
                    error = '建站失败：文件初始化出错，请重试或联系管理员'
                    if is_fragment:
                        return jsonify({'ok': False, 'error': error})
                    current_site = Site.query.filter_by(owner_id=user.id).order_by(Site.id.desc()).first()
                    return render_template('dashboard/site_new.html',
                                           user=user, site=current_site,
                                           template=template, templates=templates, form=form, error=error,
                                           template_language_map=template_language_map,
                                           template_default_language_map=template_default_language_map,
                                           active='templates')
                flash(f'已创建站点 #{site.id} ({form["slug"]})')
                if is_fragment:
                    return jsonify({'ok': True, 'redirect': url_for('core.overview', site=site.slug)})
                return redirect(url_for('core.overview', site=site.slug))

        # POST 验证失败 -> fragment 模式返回 JSON，普通模式重渲染页面
        if is_fragment:
            return jsonify({'ok': False, 'error': error})

    current_site = Site.query.filter_by(owner_id=user.id).order_by(Site.id.desc()).first()
    if is_fragment:
        return render_template('dashboard/panel_site_new.html',
                               user=user,
                               site=current_site,
                               template=template, templates=templates, form=form, error=error,
                               template_language_map=template_language_map,
                               template_default_language_map=template_default_language_map,
                               active='templates')
    return render_template('dashboard/site_new.html',
                           user=user,
                           site=current_site,
                           template=template, templates=templates, form=form, error=error,
                           template_language_map=template_language_map,
                           template_default_language_map=template_default_language_map,
                           active='templates')


@bp.route('/build', methods=['GET', 'POST'])
def build():
    """触发构建当前站点, 跳到预览首页."""
    _, site = _current_context()
    report = []
    try:
        build_site(site.id, base_url=f'/preview/{site.slug}', report=report)
    except Exception as exc:
        current_app.logger.exception('站点 %s 构建失败', site.id)
        if request.method == 'POST' or request.args.get('_fragment'):
            return jsonify({'ok': False, 'error': str(exc), 'report': report}), 500
        abort(500, f'构建失败: {exc}')

    if request.method == 'POST' or request.args.get('_fragment'):
        return jsonify({'ok': True, 'preview_url': f'/preview_site/{site.slug}', 'report': report})

    return redirect(url_for('core.preview_site', site_id=site.slug))


@bp.route('/publish', methods=['POST'])
def publish_site():
    """构建并发布当前站点，同时记录可追踪的发布状态与时间。"""
    user, site = _current_context()
    report = []
    try:
        # 正式产物按域名根目录构建，不能携带 /preview/<id>。使用独立临时目录，
        # 避免覆盖编辑器正在使用的预览产物；后续 OSS/CDN 上传直接消费此目录。
        from tempfile import TemporaryDirectory
        with TemporaryDirectory(prefix=f'publish-{site.id}-') as temp_dir:
            build_site(site.id, base_url='', report=report,
                       output_root=Path(temp_dir) / site.slug)
            if report:
                message = f'发布检查发现 {len(report)} 个页面或链接问题，请修复后重试'
                payload = {'ok': False, 'error': message, 'report': report}
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' \
                        or request.accept_mimetypes.best == 'application/json':
                    return jsonify(payload), 422
                flash(message, 'danger')
                return redirect(url_for('core.account', section='sites'))
        site.status = 'published'
        site.last_published_at = datetime.now(timezone.utc)
        _write_audit(user, 'site.publish', f'发布站点“{site.name or site.slug}”',
                     site_id=site.id, details={'report_count': len(report)})
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception('站点 %s 发布失败', site.id)
        return jsonify({'ok': False, 'error': str(exc), 'report': report}), 500
    payload = {
        'ok': True,
        'status': site.status,
        'published_at': site.last_published_at.isoformat(),
        'preview_url': f'/preview_site/{site.slug}',
        'report': report,
    }
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' \
            or request.accept_mimetypes.best == 'application/json':
        return jsonify(payload)
    flash(f'站点“{site.name or site.slug}”发布完成', 'success')
    return redirect(url_for('core.account', section='sites'))


@bp.route('/export.zip')
def export_zip():
    """导出当前站点的静态文件 ZIP."""
    from io import BytesIO
    from zipfile import ZIP_DEFLATED, ZipFile


    _, site = _current_context()
    # #13: 传入 report 收集缺页, 有失败时在 ZIP 内附一份说明, 不让店主拿到缺页站还不自知。
    report = []
    buffer = BytesIO()
    from tempfile import TemporaryDirectory
    with TemporaryDirectory(prefix=f'export-{site.id}-') as temp_dir:
        output_root = build_site(site.id, base_url='', report=report,
                                 output_root=Path(temp_dir) / site.slug)
        if report:
            message = f'导出检查发现 {len(report)} 个页面或链接问题，请修复后重试'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' \
                    or request.accept_mimetypes.best == 'application/json':
                return jsonify({'ok': False, 'error': message, 'report': report}), 422
            flash(message, 'danger')
            return redirect(url_for('core.account', section='sites'))
        with ZipFile(buffer, 'w', ZIP_DEFLATED) as zf:
            for path in output_root.rglob('*'):
                if path.is_file():
                    zf.write(path, path.relative_to(output_root).as_posix())
    buffer.seek(0)

    filename = f'{site.slug or "site"}-static.zip'
    return send_file(
        buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=filename,
    )


def _default_lang_code(site):
    """取站点默认语言，优先使用已启用的第一个语言."""
    tpl_meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    if tpl_meta_path.exists():
        tpl_meta = _yaml.safe_load(tpl_meta_path.read_text(encoding='utf-8')) or {}
        languages = tpl_meta.get('languages', [])
        if languages:
            # 按站点启用的语言过滤
            enabled_codes = site.enabled_languages or [l['code'] for l in languages]
            enabled = [l for l in languages if l['code'] in enabled_codes]
            # 兜底：如果过滤后为空，使用全部语言
            if enabled:
                return enabled[0].get('code', 'zh-CN')
            return languages[0].get('code', 'zh-CN')
    return 'zh-CN'


def _preview_needs_rebuild(site_id, out):
    """Return true when generated preview is missing or older than site/template files."""
    index = out / 'index.html'
    if not index.exists():
        return True
    try:
        built_at = index.stat().st_mtime
        root = Path(current_app.config['SITES_DIR']) / str(site_id)
        site_changed = any(
            path.stat().st_mtime > built_at
            for path in root.rglob('*.yaml')
            if not path.name.startswith('.tmp-')
        )
        if site_changed:
            return True

        site = Site.query.get(site_id)
        if not site:
            return False
        tpl_root = Path(current_app.config['TEMPLATES_DIR']) / site.template_name
        watched_suffixes = {'.html', '.yaml', '.yml', '.css', '.js', '.svg'}
        return any(
            path.stat().st_mtime > built_at
            for path in tpl_root.rglob('*')
            if path.is_file() and path.suffix.lower() in watched_suffixes
        )
    except OSError:
        return True


@bp.route('/preview_site/<site_id>')
def preview_site(site_id):
    """确保已构建，重定向到根 index.html（多语言站走 JS 浏览器语言检测）."""
    from flask import redirect, request, url_for
    site = _site_from_ref(site_id)
    if not site:
        abort(404)
    _require_site_access(site)
    if str(site_id) != site.slug:
        return redirect(url_for('core.preview_site', site_id=site.slug), code=302)
    session['current_site_id'] = site.id  # 后续 /assets/ 资源请求需要
    out = Path(current_app.config['OUTPUT_DIR']) / str(site.id)

    # 构建条件：不存在任何产出。?_ 只是浏览器 cache-busting 参数，不触发重建。
    if _preview_needs_rebuild(site.id, out):
        build_site(site.id, base_url=f'/preview/{site.slug}')

    # 返回根 index.html：多语言站走 JS 浏览器语言检测，单语言站直接渲染
    return redirect(url_for('core.preview', site_id=site.slug))


@bp.route('/preview_or_build/<site_id>')
def preview_or_build(site_id):
    """确保已构建，返回根 index.html（多语言站走 JS 浏览器语言检测）或默认语言首页."""
    site = _site_from_ref(site_id)
    if not site:
        abort(404)
    _require_site_access(site)
    if str(site_id) != site.slug:
        return redirect(url_for('core.preview_or_build', site_id=site.slug), code=302)
    session['current_site_id'] = site.id
    out = Path(current_app.config['OUTPUT_DIR']) / str(site.id)

    # 优先返回根 index.html（多语言站含 JS 浏览器语言检测），
    # 不存在则回退到默认语言首页（单语言站点无根选择页）
    root_index = out / 'index.html'
    if _preview_needs_rebuild(site.id, out):
        build_site(site.id, base_url=f'/preview/{site.slug}')

    if (out / 'index.html').exists():
        return _safe_send_from_directory(out, 'index.html')

    # 回退：单语言站点直接返回首页
    lang_code = _default_lang_code(site)
    lang_index = out / lang_code / 'index.html'
    if lang_index.exists():
        return _safe_send_from_directory(out / lang_code, 'index.html')
    return _safe_send_from_directory(out, 'index.html')


def _parse_detail_tables_form(form):
    try:
        tables_count = int(form.get('detail_tables_count', '0'))
    except (ValueError, TypeError):
        tables_count = 0
    detail_tables = []
    for ti in range(tables_count):
        try:
            row_count = int(form.get(f'detail_tables_{ti}_rows', '0'))
        except (ValueError, TypeError):
            row_count = 0
        try:
            col_count = int(form.get(f'detail_tables_{ti}_cols', '0'))
        except (ValueError, TypeError):
            col_count = 0
        rows = []
        has_content = False
        for ri in range(max(0, row_count)):
            cells = []
            for ci in range(max(0, col_count)):
                text = form.get(f'detail_tables_{ti}_r{ri}_c{ci}_text', '').strip()
                url = form.get(f'detail_tables_{ti}_r{ri}_c{ci}_url', '').strip()
                cell = {}
                if text:
                    cell['text'] = text
                if url:
                    cell['url'] = url
                if cell:
                    has_content = True
                cells.append(cell)
            rows.append({'cells': cells})
        detail_tables.append({'rows': rows, 'visible': has_content})
    return detail_tables


def _parse_key_value_items_form(form, prefix):
    try:
        count = int(form.get(f'{prefix}_count', '0'))
    except (ValueError, TypeError):
        count = 0
    items = []
    for index in range(count):
        name = form.get(f'{prefix}_{index}_name', '').strip()
        value = form.get(f'{prefix}_{index}_value', '').strip()
        if name or value:
            items.append({'name': name, 'value': value})
    return items


def _parse_detail_specs_form(form):
    try:
        group_count = int(form.get('detail_specs_count', '0'))
    except (ValueError, TypeError):
        group_count = 0
    groups = []
    for group_index in range(group_count):
        try:
            row_count = int(form.get(f'detail_specs_{group_index}_count', '0'))
        except (ValueError, TypeError):
            row_count = 0
        items = []
        for row_index in range(row_count):
            name = form.get(f'detail_specs_{group_index}_{row_index}_name', '').strip()
            desc = form.get(f'detail_specs_{group_index}_{row_index}_desc', '').strip()
            value = form.get(f'detail_specs_{group_index}_{row_index}_value', '').strip()
            if name or desc or value:
                items.append({'name': name, 'desc': desc, 'value': value})
        groups.append({'items': items, 'visible': bool(items)})
    return groups


def _parse_detail_features_form(form):
    try:
        count = int(form.get('detail_features_count', '0'))
    except (ValueError, TypeError):
        count = 0
    features = []
    for idx in range(count):
        title = form.get(f'detail_features_{idx}_title', '').strip()
        text = form.get(f'detail_features_{idx}_text', '').strip()
        icon = form.get(f'detail_features_{idx}_icon', '').strip()
        if title or text or icon:
            item = {}
            if icon:
                item['icon'] = icon
            if title:
                item['title'] = title
            if text:
                item['text'] = text
            features.append(item)
    return features


def _parse_detail_files_form(form):
    try:
        count = int(form.get('detail_files_count', '0'))
    except (ValueError, TypeError):
        count = 0
    files = []
    for idx in range(count):
        title = form.get(f'detail_files_{idx}_title', '').strip()
        url = form.get(f'detail_files_{idx}_url', '').strip()
        desc = form.get(f'detail_files_{idx}_desc', '').strip()
        file_type = form.get(f'detail_files_{idx}_type', '').strip()
        if title or url or desc or file_type:
            item = {}
            if title:
                item['title'] = title
            if url:
                item['url'] = url
            if desc:
                item['desc'] = desc
            if file_type:
                item['type'] = file_type
            files.append(item)
    return files


def _parse_detail_faqs_form(form):
    try:
        count = int(form.get('detail_faqs_count', '0'))
    except (ValueError, TypeError):
        count = 0
    faqs = []
    for idx in range(count):
        question = form.get(f'detail_faqs_{idx}_question', '').strip()
        answer = form.get(f'detail_faqs_{idx}_answer', '').strip()
        if question or answer:
            faqs.append({'question': question, 'answer': answer})
    return faqs


def _parse_detail_content_blocks_form(form, files=None, site_id=None, dataset_key='', fields=None, item=None):
    try:
        count = int(form.get('detail_content_blocks_count', '0'))
    except (ValueError, TypeError):
        count = 0
    blocks = []
    for idx in range(count):
        block_type = form.get(f'detail_content_blocks_{idx}_type', 'text').strip() or 'text'
        slot_id = form.get(f'detail_content_blocks_{idx}_slot_id', '').strip()
        title = form.get(f'detail_content_blocks_{idx}_title', '').strip()
        text = form.get(f'detail_content_blocks_{idx}_text', '').strip()
        if block_type in {'text', 'media_text'}:
            text = sanitize_richtext(text, 'content')
        elif block_type == 'note':
            text = sanitize_richtext(text, 'notice')
        image = form.get(f'detail_content_blocks_{idx}_image', '').strip()
        video = form.get(f'detail_content_blocks_{idx}_video', '').strip()
        embed_url = form.get(f'detail_content_blocks_{idx}_embed_url', '').strip()
        note_style = form.get(f'detail_content_blocks_{idx}_note_style', 'info').strip() or 'info'
        table_text = form.get(f'detail_content_blocks_{idx}_table_text', '').strip()
        try:
            table_rows_count = max(0, int(form.get(f'detail_content_blocks_{idx}_table_rows', '0') or 0))
        except (TypeError, ValueError):
            table_rows_count = 0
        try:
            table_cols_count = max(0, int(form.get(f'detail_content_blocks_{idx}_table_cols', '0') or 0))
        except (TypeError, ValueError):
            table_cols_count = 0
        alt = form.get(f'detail_content_blocks_{idx}_alt', '').strip()
        caption = form.get(f'detail_content_blocks_{idx}_caption', '').strip()
        if block_type == 'video':
            caption = caption or text
            text = ''
        layout = form.get(f'detail_content_blocks_{idx}_layout', 'image_left').strip() or 'image_left'
        image_upload = files.get(f'detail_content_blocks_{idx}_image_file') if files else None
        video_upload = files.get(f'detail_content_blocks_{idx}_video_file') if files else None
        if image_upload and image_upload.filename and site_id:
            try:
                image = _save_uploaded_image(site_id, image_upload, prefix=f'{dataset_key}-content-{idx + 1}')
                alt = alt or _context_alt(fields or {}, item or {}, fallback=_filename_alt(image_upload))
            except Exception as exc:
                current_app.logger.warning('详情内容图片上传失败: %s', exc)
        if video_upload and video_upload.filename and site_id:
            try:
                video = _save_uploaded_media(site_id, video_upload, prefix=f'{dataset_key}-content-video-{idx + 1}')
            except Exception as exc:
                current_app.logger.warning('详情内容视频上传失败: %s', exc)
        gallery = []
        for gi in range(6):
            gallery_image = form.get(f'detail_content_blocks_{idx}_gallery_{gi}_image', '').strip()
            gallery_alt = form.get(f'detail_content_blocks_{idx}_gallery_{gi}_alt', '').strip()
            gallery_caption = form.get(f'detail_content_blocks_{idx}_gallery_{gi}_caption', '').strip()
            gallery_upload = files.get(f'detail_content_blocks_{idx}_gallery_{gi}_image_file') if files else None
            if gallery_upload and gallery_upload.filename and site_id:
                try:
                    gallery_image = _save_uploaded_image(site_id, gallery_upload, prefix=f'{dataset_key}-content-gallery-{idx + 1}-{gi + 1}')
                    gallery_alt = gallery_alt or _context_alt(fields or {}, item or {}, fallback=_filename_alt(gallery_upload))
                except Exception as exc:
                    current_app.logger.warning('详情内容多图上传失败: %s', exc)
            if gallery_image:
                gallery_item = {'image': gallery_image}
                if gallery_alt:
                    gallery_item['alt'] = gallery_alt
                if gallery_caption:
                    gallery_item['caption'] = gallery_caption
                gallery.append(gallery_item)
        table_cells = []
        if table_rows_count and table_cols_count:
            for tr in range(table_rows_count):
                row = []
                row_has_value = False
                for tc in range(table_cols_count):
                    cell = form.get(f'detail_content_blocks_{idx}_table_{tr}_{tc}', '').strip()
                    if cell:
                        row_has_value = True
                    row.append(cell)
                if row_has_value:
                    table_cells.append(row)
        block = {'type': block_type}
        if slot_id:
            block['slot_id'] = slot_id
        if title:
            block['title'] = title
        if text:
            block['text'] = text
        if image:
            block['image'] = image
        if video:
            block['video'] = video
        if embed_url:
            block['embed_url'] = embed_url
        if gallery:
            block['images'] = gallery
        if table_cells:
            block['table'] = table_cells
            block['table_rows'] = table_rows_count
            block['table_cols'] = table_cols_count
        elif table_text:
            block['table_text'] = table_text
        if block_type == 'note':
            block['style'] = note_style
        if alt:
            block['alt'] = alt
        if caption:
            block['caption'] = caption
        if block_type == 'media_text':
            block['layout'] = layout
        if len(block) > 1:
            blocks.append(block)
    return blocks


def _parse_detail_actions_form(form):
    """Parse the fixed detail-page primary/secondary action fields."""
    actions = {}
    for variant in ('primary', 'secondary'):
        text = form.get(f'detail_action_{variant}_text', '').strip()
        url = form.get(f'detail_action_{variant}_url', '').strip()
        if text or url:
            actions[variant] = {'text': text, 'url': url}
    return actions


def _parse_dataset_draft_item(site, dataset_key, item_id, form, storage_lang, source_storage_lang):
    """Parse a dataset edit form into one draft item without writing YAML."""
    item = datasets.find(site.id, dataset_key, item_id, lang=storage_lang)
    source_item = datasets.find(site.id, dataset_key, item_id, lang=source_storage_lang)
    if not item and source_item:
        item = source_item
    if not item:
        return None

    fields = {}
    for key, val in item.items():
        if key not in ('modules', 'csrf_token') and not key.startswith('_draft_'):
            fields[key] = val

    for key in form:
        if key.startswith('_draft_'):
            continue
        if key.startswith('detail_gallery_') or key in ('detail_gallery_count',):
            continue
        if key == '_show_detail_btn_mode':
            continue
        if key in ('_advanced_modules_enabled', '_restore_template_modules'):
            continue
        if key.startswith('specs_') or key in ('specs_count',):
            continue
        if key.startswith('detail_specs_') or key in ('detail_specs_count',):
            continue
        if key.startswith('parameters_') or key in ('parameters_count',):
            continue
        if key.startswith('attributes_') or key in ('attributes_count',):
            continue
        if key.startswith('detail_action_'):
            continue
        if key.startswith('detail_links_') or key in ('detail_links_count',):
            continue
        if key.startswith('detail_tables_') or key in ('detail_tables_count',):
            continue
        if key.startswith('detail_features_') or key in ('detail_features_count',):
            continue
        if key.startswith('detail_files_') or key in ('detail_files_count',):
            continue
        if key.startswith('detail_faqs_') or key in ('detail_faqs_count',):
            continue
        if key.startswith('detail_content_blocks_') or key in ('detail_content_blocks_count',):
            continue
        if key.startswith('module_') or key.startswith('_') or key in ('module_count', 'csrf_token'):
            continue
        fields[key] = form.get(key, '').strip()

    detail_btn_mode = form.get('_show_detail_btn_mode')
    if detail_btn_mode == 'inherit':
        fields.pop('show_detail_btn', None)
    elif detail_btn_mode in ('true', 'false'):
        fields['show_detail_btn'] = detail_btn_mode == 'true'

    if any(key.startswith('detail_action_') for key in form):
        fields['detail_actions'] = _parse_detail_actions_form(form)

    if 'tags' in fields:
        fields['tags'] = _parse_tags_input(fields.get('tags'))

    if 'tags_visible' in fields:
        fields['tags_visible'] = str(fields.get('tags_visible')).lower() != 'false'

    if 'detail_gallery_count' in form or 'detail_gallery_visible' in form:
        try:
            gallery_count = int(form.get('detail_gallery_count', '0'))
        except (ValueError, TypeError):
            gallery_count = 0
        gallery_images = []
        for gi in range(gallery_count):
            url = form.get(f'detail_gallery_{gi}_url', '').strip()
            alt = form.get(f'detail_gallery_{gi}_url_alt', '').strip()
            if url:
                image = {'url': url}
                if alt:
                    image['alt'] = alt
                gallery_images.append(image)
        fields['detail_gallery'] = {
            'visible': str(form.get('detail_gallery_visible', 'true')).lower() != 'false',
            'images': gallery_images,
        }

    for source_prefix in ('specs', 'parameters', 'attributes'):
        if f'{source_prefix}_count' in form:
            fields[source_prefix] = _parse_key_value_items_form(form, source_prefix)
    if 'detail_specs_count' in form:
        fields['detail_specs'] = _parse_detail_specs_form(form)

    if 'detail_links_count' in form:
        try:
            links_count = int(form.get('detail_links_count', '0'))
        except (ValueError, TypeError):
            links_count = 0
        if links_count > 0:
            detail_links = []
            for li in range(links_count):
                text = form.get(f'detail_links_{li}_text', '').strip()
                url = form.get(f'detail_links_{li}_url', '').strip()
                if text or url:
                    detail_links.append({'text': text, 'url': url})
            fields['detail_links'] = detail_links
            if detail_links:
                fields['link_text'] = detail_links[0].get('text', '')
                fields['link_url'] = detail_links[0].get('url', '')

    if 'detail_tables_count' in form:
        fields['detail_tables'] = _parse_detail_tables_form(form)
    if 'detail_features_count' in form:
        fields['detail_features'] = _parse_detail_features_form(form)
    if 'detail_files_count' in form:
        fields['detail_files'] = _parse_detail_files_form(form)
    if 'detail_faqs_count' in form:
        fields['detail_faqs'] = _parse_detail_faqs_form(form)
    if 'detail_content_blocks_count' in form:
        fields['detail_content_blocks'] = _parse_detail_content_blocks_form(form, fields=fields, item=item)

    settings_for_templates = read_yaml(site.id, 'settings.yaml') or {}
    raw_menu_for_templates = settings_for_templates.get('menu') or []
    list_targets_for_templates = menu_lib.collect_list_targets(menu_lib.normalize_for_render(raw_menu_for_templates))
    page_label_for_templates = next(
        (entry.get('label') for entry in list_targets_for_templates if entry.get('target') == dataset_key),
        dataset_key,
    )
    page_cfg_for_templates = _ensure_page_detail_templates(site.id, dataset_key, page_label_for_templates)
    templates_for_autofill = _detail_templates_for_page(page_cfg_for_templates, dataset_key, page_label_for_templates)
    template_for_autofill = next(
        (tpl for tpl in templates_for_autofill if str(tpl.get('id') or '') == str(fields.get('template_id') or '')),
        None,
    )
    if template_for_autofill is None:
        default_template_id_for_autofill = _default_detail_template_id(page_cfg_for_templates, dataset_key, page_label_for_templates)
        template_for_autofill = next(
            (tpl for tpl in templates_for_autofill if str(tpl.get('id') or '') == str(default_template_id_for_autofill)),
            None,
        )
    _apply_detail_template_autofill(fields, template_for_autofill or {}, page_label_for_templates)

    force_template_preview = form.get('_draft_force_template_preview') == '1'
    if force_template_preview or form.get('_restore_template_modules') == '1':
        fields['modules'] = []
    module_count_str = form.get('module_count')
    if not force_template_preview and form.get('_restore_template_modules') != '1' and form.get('_advanced_modules_enabled') == '1' and module_count_str and module_count_str.isdigit():
        existing_modules = item.get('modules', [])
        modules = _parse_modules_form(form, existing_modules)
        for m in modules:
            if m.get('type') == 'item_data':
                keep = {}
                for key, value in (m.get('data') or {}).items():
                    if key.startswith('style_'):
                        fields[key] = value
                    else:
                        keep[key] = value
                m['data'] = keep
        fields['modules'] = modules
    elif not force_template_preview and form.get('_restore_template_modules') != '1' and form.get('_advanced_modules_enabled') == '1' and module_count_str is not None:
        fields['modules'] = []

    draft = dict(item)
    draft.update(fields)
    draft['id'] = item_id
    return draft


def _live_preview_content_version(site):
    """Cheap invalidation token for GET live-preview cache."""
    version_key = (site.id, site.template_name)
    cached = _LIVE_PREVIEW_VERSION_CACHE.get(version_key)
    now = time.monotonic()
    if cached and now - cached[0] <= _LIVE_PREVIEW_VERSION_TTL:
        return cached[1]
    latest = 0
    site_root = Path(current_app.config['SITES_DIR']) / str(site.id)
    tpl_root = Path(current_app.config['TEMPLATES_DIR']) / site.template_name
    watched_suffixes = {'.yaml', '.yml', '.html', '.css', '.js'}
    for root in (site_root, tpl_root):
        try:
            for path in root.rglob('*'):
                if not path.is_file() or path.name.startswith('.tmp-'):
                    continue
                if path.suffix.lower() not in watched_suffixes:
                    continue
                try:
                    latest = max(latest, path.stat().st_mtime_ns)
                except OSError:
                    continue
        except OSError:
            continue
    _LIVE_PREVIEW_VERSION_CACHE[version_key] = (now, latest)
    return latest


def _live_preview_cache_get(key):
    item = _LIVE_PREVIEW_CACHE.get(key)
    if not item:
        return None
    created_at, html = item
    if time.monotonic() - created_at > _LIVE_PREVIEW_CACHE_TTL:
        _LIVE_PREVIEW_CACHE.pop(key, None)
        return None
    return html


def _live_preview_cache_set(key, html):
    if len(_LIVE_PREVIEW_CACHE) >= _LIVE_PREVIEW_CACHE_MAX:
        oldest = min(_LIVE_PREVIEW_CACHE.items(), key=lambda item: item[1][0])[0]
        _LIVE_PREVIEW_CACHE.pop(oldest, None)
    _LIVE_PREVIEW_CACHE[key] = (time.monotonic(), html)


@bp.route('/live_preview/<site_id>/')
@bp.route('/live_preview/<site_id>/<path:filepath>', methods=['GET', 'POST'])
def live_preview(site_id, filepath='index.html'):
    """Editor live preview: render one page without running the full static build."""
    site_ref = site_id
    site = _site_from_ref(site_ref)
    if not site:
        abort(404)
    _require_site_access(site)
    if request.method == 'GET' and str(site_ref) != site.slug:
        canonical = url_for('core.live_preview', site_id=site.slug, filepath=filepath)
        if request.query_string:
            canonical += '?' + request.query_string.decode('utf-8', errors='ignore')
        return redirect(canonical, code=302)
    session['current_site_id'] = site.id
    site_id = site.id

    filepath = (filepath or 'index.html').replace('\\', '/').lstrip('/')
    if filepath.startswith('static/'):
        static_file = filepath[len('static/'):]
        tpl_static = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'static'
        return _safe_send_from_directory(tpl_static, static_file)

    if filepath in ('', 'index.html'):
        return redirect(url_for('core.live_preview',
                                site_id=site.slug,
                                filepath=f'{_default_lang_code(site)}/index.html'))

    cache_key = None
    if request.method == 'GET':
        cache_key = (
            site_id,
            filepath,
            request.args.get('pv', ''),
            _live_preview_content_version(site),
        )
        cached_html = _live_preview_cache_get(cache_key)
        if cached_html is not None:
            return current_app.response_class(cached_html, mimetype='text/html; charset=utf-8')

    draft_page = None
    draft_data = None
    draft_page_key = request.form.get('_draft_page_key', '').strip()
    if request.method == 'POST' and draft_page_key:
        _validate_key(draft_page_key)
        lang, _languages, default_lang = _get_panel_lang(site)
        storage_lang = _storage_lang(site, lang, default_lang)
        page = read_yaml(site.id, f'pages/{draft_page_key}.yaml', lang=storage_lang) or {}
        existing_modules = page.get('modules', [])
        if storage_lang and not existing_modules:
            source_storage_lang = _storage_lang(site, default_lang, default_lang)
            source_page = read_yaml(site.id, f'pages/{draft_page_key}.yaml', lang=source_storage_lang) or {}
            existing_modules = source_page.get('modules', []) or existing_modules
        draft_page = dict(page)
        draft_page['modules'] = _parse_modules_form(request.form, existing_modules)
        if 'page_title' in request.form:
            title = request.form.get('page_title', '').strip()
            if title:
                draft_page['title'] = title
            else:
                draft_page.pop('title', None)
        if 'page_description' in request.form:
            description = request.form.get('page_description', '').strip()
            if description:
                draft_page['description'] = description
            else:
                draft_page.pop('description', None)

    draft_dataset_key = request.form.get('_draft_dataset_key', '').strip()
    draft_item_id = request.form.get('_draft_item_id', '').strip()
    if request.method == 'POST' and draft_dataset_key and draft_item_id.isdigit():
        _validate_key(draft_dataset_key)
        lang, _languages, default_lang = _get_panel_lang(site)
        storage_lang = _storage_lang(site, lang, default_lang)
        source_storage_lang = _storage_lang(site, default_lang, default_lang)
        item_id = int(draft_item_id)
        draft_item = _parse_dataset_draft_item(
            site, draft_dataset_key, item_id, request.form, storage_lang, source_storage_lang
        )
        if draft_item:
            items = datasets.load(site.id, draft_dataset_key, lang=storage_lang)
            if not items and storage_lang:
                items = datasets.load(site.id, draft_dataset_key, lang=source_storage_lang)
            draft_items = []
            replaced = False
            for item in items or []:
                if item.get('id') == item_id:
                    draft_items.append(draft_item)
                    replaced = True
                else:
                    draft_items.append(item)
            if not replaced:
                draft_items.append(draft_item)
            draft_data = {draft_dataset_key: draft_items}

    try:
        html = render_site_page(
            site_id,
            filepath=filepath,
            base_url=f'/live_preview/{site.slug}',
            draft_page_key=draft_page_key or None,
            draft_page=draft_page,
            draft_data=draft_data,
        )
    except FileNotFoundError:
        abort(404, '未找到可实时预览的页面')
    except Exception as exc:
        current_app.logger.exception('实时预览渲染站点 %s 失败', site_id)
        abort(500, f'实时预览失败: {exc}')
    if cache_key is not None:
        _live_preview_cache_set(cache_key, html)
    return current_app.response_class(html, mimetype='text/html; charset=utf-8')


@bp.route('/preview/<site_id>/')
@bp.route('/preview/<site_id>/<path:filepath>')
def preview(site_id, filepath='index.html'):
    """预览 output/<site_id>/ 下的静态文件，自动构建."""
    site_ref = site_id
    site = _site_from_ref(site_ref)
    if not site:
        abort(404)
    _require_site_access(site)
    if str(site_ref) != site.slug:
        canonical = url_for('core.preview', site_id=site.slug, filepath=filepath)
        if request.query_string:
            canonical += '?' + request.query_string.decode('utf-8', errors='ignore')
        return redirect(canonical, code=302)
    session['current_site_id'] = site.id  # 后续 /assets/ 资源请求需要
    site_id = site.id
    out = Path(current_app.config['OUTPUT_DIR']) / str(site.id)
    parts = [part for part in str(filepath).replace('\\', '/').split('/') if part]
    if parts:
        asset_index = 0 if parts[0] == 'assets' else (1 if len(parts) > 1 and parts[1] == 'assets' else -1)
        if asset_index >= 0:
            asset_path = '/'.join(parts[asset_index + 1:])
            return _safe_send_from_directory(out / 'assets', asset_path)

    # 根路径请求 → 返回根 index.html（多语言站走 JS 浏览器语言检测），不再跳默认语言
    if filepath == 'index.html':
        if _preview_needs_rebuild(site_id, out):
            try:
                build_site(site.id, base_url=f'/preview/{site.slug}')
            except Exception:
                current_app.logger.exception('预览构建站点 %s 失败', site_id)
        if (out / 'index.html').exists():
            return _safe_send_from_directory(out, 'index.html')
    elif _preview_needs_rebuild(site_id, out):
        try:
            build_site(site.id, base_url=f'/preview/{site.slug}')
        except Exception:
            current_app.logger.exception('预览构建站点 %s 失败', site_id)

    # 先解析出最终目标文件，再判断是否需要重建
    full = out / filepath
    if full.is_dir():
        full = full / 'index.html'
        filepath = f'{filepath.rstrip("/")}/index.html'
    if not full.exists():
        try:
            build_site(site.id, base_url=f'/preview/{site.slug}')
        except Exception:
            current_app.logger.exception('预览构建站点 %s 失败', site_id)  # #15: 留痕
    if not out.exists():
        out.mkdir(parents=True, exist_ok=True)
    if not full.exists():
        # 尝试默认语言子目录
        for sub in out.iterdir():
            if sub.is_dir() and (sub / 'index.html').exists():
                return _safe_send_from_directory(out, f'{sub.name}/index.html')
        abort(404, '未生成页面，请检查模板数据')
    return _safe_send_from_directory(out, filepath)


def _get_panel_lang(site):
    """从请求参数获取面板当前编辑语言, 默认返回模板的默认语言.

    只返回站点已启用的语言列表，未启用的不显示在面板语言标签中.
    """
    meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    all_languages = []
    default_lang = 'zh-CN'
    if meta_path.exists():
        meta = _yaml.safe_load(meta_path.read_text(encoding='utf-8')) or {}
        all_languages = meta.get('languages', [])
        default_lang = meta.get('default_language', all_languages[0]['code'] if all_languages else 'zh-CN')

    # 按站点启用的语言过滤（从 DB enabled_languages 读取，兜底显示全部）
    enabled_codes = site.enabled_languages or [l['code'] for l in all_languages]
    languages = [l for l in all_languages if l['code'] in enabled_codes]
    # 兜底：如果过滤后为空（旧站点 enabled_languages 可能与模板不一致），使用全部语言
    if not languages:
        languages = all_languages

    lang = request.args.get('lang', '').strip()
    valid_codes = {l['code'] for l in languages}
    if lang and lang in valid_codes:
        return lang, languages, default_lang
    return default_lang, languages, default_lang


def _storage_lang(site, lang, default_lang):
    """返回语言内容的实际存储路径参数.

    与 builder._load_lang_overrides 的逻辑对齐:
    - 非默认语言: 始终返回 lang 参数 (读写 lang/<code>/ 子目录)
    - 默认语言: 如果 lang/<default_lang>/ 目录存在, 返回 lang 参数;
      否则返回 None (读写根目录)

    这是什么场景: 当站点根目录 pages/ 存的是旧默认语言 (如英文),
    而新默认语言 (如中文) 存在于 lang/zh-CN/ 时, 后台面板需要从
    语言子目录读写, 而不是从根目录读到旧语言内容.
    """
    if lang != default_lang:
        return lang
    if lang_root(site.id, lang).exists():
        return lang
    return None


def _lang_key(base_key, site, lang, default_lang):
    """返回 settings.yaml 中带语言后缀的 key (company/contact/footer).

    与构建器对齐: 如果 lang/<lang>/ 目录存在, 始终用 "{key}_{lang}" 后缀 key.
    否则默认语言用根 key, 非默认语言才带后缀.

    为什么: 当根 company/contact 存的是旧默认语言 (如英文),
    company_zh-CN/contact_zh-CN 存的是新默认语言 (如中文) 时,
    构建器优先取 _zh-CN 版本, 面板也必须读写同一个 key.
    """
    if lang_root(site.id, lang).exists():
        return f'{base_key}_{lang}'
    if lang == default_lang:
        return base_key
    return f'{base_key}_{lang}'


def _merge_settings_section(shared, localized):
    """Merge shared settings with current-language overrides."""
    if not isinstance(shared, dict):
        shared = {}
    if not isinstance(localized, dict):
        localized = {}
    shared_first_fields = {'logo', 'favicon', 'icp', 'phone', 'mobile', 'email', 'wechat'}
    result = dict(shared)
    for key, value in localized.items():
        if key in shared_first_fields and result.get(key):
            continue
        if value not in (None, ''):
            result[key] = value
    return result


def _render(template_name, **kwargs):
    """渲染模板, 顺带注入图标列表和样式注册表(供面板表单用)。

    #19: 原来按 ?_fragment 分两支但两支完全相同(伪分支), docstring 也误导。
    fragment 与整页用的是同一个 template_name, 调用方自行传不同模板名, 这里不分支。
    """
    from .icon_registry import ICON_REGISTRY, icon_names
    from .style_registry import STYLE_REGISTRY
    kwargs.setdefault('icon_list', icon_names())
    kwargs.setdefault('icon_registry', ICON_REGISTRY)
    kwargs.setdefault('style_registry', STYLE_REGISTRY)
    return render_template(template_name, **kwargs)


@bp.route('/api/translate', methods=['POST'])
@csrf.exempt  # 只读翻译端点，无数据修改，免除 CSRF 保护（fetch+JSON 调用不含表单 token）
def api_translate():
    """AI 翻译端点 — 接受 JSON 文本字典，返回翻译后的字典."""
    data = request.get_json(silent=True) or {}
    texts = data.get('texts', {})
    source_lang = data.get('source_lang', 'zh-CN')
    target_lang = data.get('target_lang', 'en')

    if not texts or not isinstance(texts, dict):
        return {'error': '请提供 texts 字典'}, 400
    if len(texts) > 50:
        return {'error': '单次最多翻译 50 个字段'}, 400

    try:
        translated = translate_json(texts, source_lang, target_lang)
        return {'ok': True, 'translated': translated}
    except ValueError as e:
        return {'error': str(e)}, 400
    except RuntimeError as e:
        return {'error': str(e)}, 502
    except Exception as e:
        current_app.logger.error('翻译失败: %s', e)
        return {'error': '翻译失败，请稍后重试'}, 500


@bp.route('/api/richtext/upload-image', methods=['POST'])
def api_richtext_upload_image():
    """Upload an image for rich-text editors and return a site-local URL."""
    _, site = _current_context()
    upload = request.files.get('image')
    if not upload or not upload.filename:
        return jsonify({'error': 'No image file provided'}), 400
    try:
        url = _save_uploaded_image(site.id, upload, prefix='richtext')
    except Exception as exc:
        current_app.logger.warning('rich text image upload failed: %s', exc)
        return jsonify({'error': str(exc)}), 400
    return jsonify({'ok': True, 'url': url})


@bp.route('/api/richtext/upload-video', methods=['POST'])
def api_richtext_upload_video():
    """Upload a video for rich-text editors and return a site-local URL."""
    _, site = _current_context()
    upload = request.files.get('video') or request.files.get('media')
    if not upload or not upload.filename:
        return jsonify({'error': 'No video file provided'}), 400
    url = _save_uploaded_media(site.id, upload, prefix='richtext-video')
    if not url:
        return jsonify({'error': 'Video upload failed or file type is not supported'}), 400
    return jsonify({'ok': True, 'url': url})


@bp.route('/api/richtext/upload-package', methods=['POST'])
def api_richtext_upload_package():
    """Upload a zip webpage package for rich-text iframe embeds."""
    _, site = _current_context()
    upload = request.files.get('package') or request.files.get('media')
    if not upload or not upload.filename:
        return jsonify({'error': 'No package file provided'}), 400
    try:
        result = _save_media_package(site.id, upload)
    except Exception as exc:
        current_app.logger.warning('rich text package upload failed: %s', exc)
        return jsonify({'error': str(exc)}), 400
    return jsonify({'ok': True, 'url': result.get('url') or result.get('entry_url'), 'name': result.get('name')})


@bp.route('/api/site/<site_id>/dataset/<string:dataset_name>/items')
def api_dataset_items(site_id, dataset_name):
    """返回某数据集下的条目摘要（供精选推荐等模块的"从数据集选取"功能调用）。

    返回 JSON 数组，每条包含 id/title/cover/summary/slug/category 等轻量字段，
    前端选取器据此展示列表、自动填入表单。
    """
    user, site = _current_context()
    requested_site = _site_from_ref(site_id)
    if not user or not requested_site or site.id != requested_site.id:
        abort(404)
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    try:
        items = datasets.load(site.id, dataset_name, lang=storage_lang)
    except Exception:
        return jsonify({'error': f'无法加载数据集: {dataset_name}'}), 404
    # 提取轻量摘要字段（名称有多种可能：title / name、cover / image / photo）
    result = []
    for it in items:
        title = it.get('title') or it.get('name') or ''
        cover = it.get('cover') or it.get('image') or it.get('photo') or ''
        summary = it.get('summary') or it.get('excerpt') or it.get('description') or ''
        slug = it.get('slug', '')
        category = it.get('category', '')
        result.append({
            'id': it.get('id'),
            'title': str(title).strip(),
            'cover': str(cover).strip(),
            'summary': str(summary).strip(),
            'slug': str(slug).strip(),
            'category': str(category).strip(),
        })
    return jsonify({'dataset': dataset_name, 'items': result})


@bp.route('/_dataset/<path:dataset_key>')
def dataset_panel(dataset_key):
    """通用数据集管理面板 — 支持 ?lang= 参数编辑不同语言版本."""
    _validate_key(dataset_key)
    user, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    items = datasets.load(site.id, dataset_key, lang=storage_lang)
    if storage_lang:
        source_storage_lang = _storage_lang(site, default_lang, default_lang)
        source_items = datasets.load(site.id, dataset_key, lang=source_storage_lang)
        if not items and source_items:
            items = source_items
    # 计算数据集的菜单层级路径，用于中间预览 URL
    settings = read_yaml(site.id, 'settings.yaml') or {}
    menu_items = settings.get('menu') or []
    from app.core.menu import find_menu_path
    meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    meta = _yaml.safe_load(meta_path.read_text(encoding='utf-8')) if meta_path.exists() else {}
    raw_menu = menu_lib.upgrade_old_format(menu_items, meta.get('datasets', []))
    preview_path = find_menu_path(raw_menu, dataset_key)
    all_list_datasets = menu_lib.collect_list_targets(menu_lib.normalize_for_render(raw_menu))
    blocks = _get_available_blocks(site.template_name)
    from .icon_registry import icon_names
    return _render('dashboard/panel_data_list.html',
                   user=user, site=site,
                   dataset_key=dataset_key, items=items,
                   blocks=blocks,
                   all_list_datasets=all_list_datasets,
                   icon_list=icon_names(),
                   edit_prefix=f'_dataset/{dataset_key}',
                   current_lang=lang, languages=languages, default_lang=default_lang,
                   preview_path=preview_path,
                   active=dataset_key)


@bp.route('/content/templates/<path:dataset_key>', methods=['GET', 'POST'], endpoint='detail_templates_workspace')
@bp.route('/_detail_templates/<path:dataset_key>', methods=['GET', 'POST'])
def detail_templates_panel(dataset_key):
    """Manage dataset detail templates stored on pages/<dataset_key>.yaml."""
    workspace_mode = request.endpoint == 'core.detail_templates_workspace'
    detail_templates_endpoint = 'core.detail_templates_workspace' if workspace_mode else 'core.detail_templates_panel'
    _validate_key(dataset_key)
    user, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    settings = read_yaml(site.id, 'settings.yaml') or {}
    menu_items = settings.get('menu') or []
    meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    meta = _yaml.safe_load(meta_path.read_text(encoding='utf-8')) if meta_path.exists() else {}
    raw_menu = menu_lib.upgrade_old_format(menu_items, meta.get('datasets', []))
    page_label = next(
        (entry.get('label') for entry in menu_lib.collect_list_targets(raw_menu) if entry.get('target') == dataset_key),
        dataset_key,
    )
    page = _ensure_page_detail_templates(site.id, dataset_key, page_label)

    if request.method == 'POST':
        page = _ensure_page_detail_templates(site.id, dataset_key, page_label)
        templates = _detail_templates_for_page(page, dataset_key, page_label)
        action = request.form.get('_template_action', request.form.get('action', '')).strip()
        template_id = request.form.get('template_id', '').strip()
        redirect_template_id = ''

        if action == 'add':
            name = request.form.get('name', '').strip() or f'{page_label}详情模板'
            new_template = _blank_detail_template(dataset_key, name)
            new_template['id'] = _unique_detail_template_id(templates, name)
            new_template['name'] = name
            templates.append(new_template)
            redirect_template_id = new_template['id']
            flash('已创建详情模板')
        elif action == 'copy':
            source = next((tpl for tpl in templates if str(tpl.get('id') or '') == template_id), None)
            if not source:
                flash('要复制的模板不存在', 'error')
            else:
                name = request.form.get('name', '').strip() or f"{source.get('name') or template_id} 副本"
                new_template = copy.deepcopy(source)
                new_template['id'] = _unique_detail_template_id(templates, name)
                new_template['name'] = name
                new_template['is_default'] = False
                templates.append(new_template)
                redirect_template_id = new_template['id']
                flash('已复制详情模板')
        elif action == 'set_default':
            found = False
            for tpl in templates:
                is_match = str(tpl.get('id') or '') == template_id
                tpl['is_default'] = is_match
                found = found or is_match
            if found:
                flash('已设置默认详情模板')
            else:
                flash('模板不存在', 'error')
        elif action == 'delete':
            source = next((tpl for tpl in templates if str(tpl.get('id') or '') == template_id), None)
            if not source:
                flash('要删除的模板不存在', 'error')
            elif source.get('is_default') is True or str(source.get('is_default')).lower() == 'true':
                flash('默认模板不能删除，请先设置其他模板为默认', 'error')
            elif len(templates) <= 1:
                flash('至少需要保留一个详情模板', 'error')
            else:
                page['detail_templates'] = [tpl for tpl in templates if str(tpl.get('id') or '') != template_id]
                write_yaml(site.id, f'pages/{dataset_key}.yaml', page)
                flash('已删除详情模板')
                redirect_args = {'dataset_key': dataset_key, 'site': site.id, 'lang': lang}
                if not workspace_mode:
                    redirect_args['_fragment'] = '1'
                return redirect(url_for(detail_templates_endpoint, **redirect_args))
        elif action == 'save_modules':
            source = next((tpl for tpl in templates if str(tpl.get('id') or '') == template_id), None)
            if not source:
                flash('要编辑的模板不存在', 'error')
            else:
                name = request.form.get('name', '').strip()
                if name:
                    source['name'] = name
                existing_modules = source.get('modules') if isinstance(source.get('modules'), list) else []
                modules = _parse_modules_form(request.form, existing_modules)
                source['modules'] = modules
                seo_title = request.form.get('seo_title', '').strip()
                seo_description = request.form.get('seo_description', '').strip()
                seo_image = request.form.get('seo_image', '').strip()
                source['seo'] = {
                    'title': seo_title or '{title} - {site_name}',
                    'description': seo_description or '{summary}',
                    'image': seo_image or 'cover',
                }
                flash('已保存详情模板')
        else:
            flash('未知操作', 'error')

        page['detail_templates'] = templates
        write_yaml(site.id, f'pages/{dataset_key}.yaml', page)
        redirect_args = {'dataset_key': dataset_key, 'site': site.id, 'lang': lang}
        if not workspace_mode:
            redirect_args['_fragment'] = '1'
        if redirect_template_id:
            redirect_args['template_id'] = redirect_template_id
        elif action == 'save_modules' and template_id:
            redirect_args['template_id'] = template_id
        return redirect(url_for(detail_templates_endpoint, **redirect_args))

    templates = _detail_templates_for_page(page, dataset_key, page_label)
    default_template_id = _default_detail_template_id(page, dataset_key, page_label)
    edit_template_id = request.args.get('template_id', '').strip()
    edit_template = next(
        (tpl for tpl in templates if str(tpl.get('id') or '') == edit_template_id),
        None,
    ) if edit_template_id else None
    blocks = _get_detail_template_components(site.template_name)
    all_list_datasets = menu_lib.collect_list_targets(menu_lib.normalize_for_render(raw_menu))
    storage_lang = _storage_lang(site, lang, default_lang)
    dataset_items = datasets.load(site.id, dataset_key, lang=storage_lang)
    template_usage = {}
    for item in dataset_items or []:
        if not isinstance(item, dict):
            continue
        tpl_id = str(item.get('template_id') or default_template_id)
        template_usage[tpl_id] = template_usage.get(tpl_id, 0) + 1
    from .style_registry import STYLE_REGISTRY
    from .icon_registry import icon_names
    template_name = 'dashboard/detail_templates_workspace.html' if workspace_mode else 'dashboard/panel_detail_templates.html'
    return _render(template_name,
                   user=user, site=site,
                   dataset_key=dataset_key,
                   page_label=page_label,
                   detail_templates=templates,
                   default_template_id=default_template_id,
                   edit_template=edit_template,
                   blocks=blocks,
                   all_list_datasets=all_list_datasets,
                   template_usage=template_usage,
                   style_registry=STYLE_REGISTRY,
                   icon_list=icon_names(),
                   current_lang=lang,
                   languages=languages,
                   default_lang=default_lang,
                   workspace_mode=workspace_mode,
                   detail_templates_endpoint=detail_templates_endpoint,
                   active=dataset_key)


@bp.route('/_dataset/<path:dataset_key>/new', methods=['POST'])
def dataset_new(dataset_key):
    """通用数据集新建条目 — 支持 ?lang= 参数保存到对应语言."""
    _validate_key(dataset_key)
    _, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    page_cfg = _ensure_page_detail_templates(site.id, dataset_key)
    default_template_id = _default_detail_template_id(page_cfg, dataset_key)
    n = len(datasets.load(site.id, dataset_key, lang=storage_lang)) + 1
    new_id = datasets.add(site.id, dataset_key, {
        'title': f'新条目 {n}', 'slug': f'item-{n}', 'template_id': default_template_id,
    }, lang=storage_lang)
    return redirect(url_for('core.dataset_panel', dataset_key=dataset_key, _fragment='1', site=site.id, lang=lang))

@bp.route('/content/edit/<path:dataset_key>/<int:item_id>', methods=['GET', 'POST'], endpoint='content_item_workspace')
@bp.route('/_dataset/<path:dataset_key>/<int:item_id>/edit', methods=['GET', 'POST'])
def dataset_edit(dataset_key, item_id):
    """通用数据集编辑 — 支持 ?lang= 参数编辑不同语言版本."""
    workspace_mode = request.endpoint == 'core.content_item_workspace'
    dataset_edit_endpoint = 'core.content_item_workspace' if workspace_mode else 'core.dataset_edit'
    _validate_key(dataset_key)
    user, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    source_storage_lang = _storage_lang(site, default_lang, default_lang)

    is_new_content = workspace_mode and item_id == 0
    copy_from_raw = (
        request.form.get('_copy_from', '').strip()
        if request.method == 'POST'
        else request.args.get('copy_from', '').strip()
    ) if is_new_content else ''
    if copy_from_raw and not copy_from_raw.isdigit():
        abort(400, '副本来源无效')
    copy_from_id = int(copy_from_raw) if copy_from_raw else 0
    is_duplicate_content = bool(copy_from_id)
    if is_new_content:
        template_id = (
            request.form.get('template_id', '').strip()
            if request.method == 'POST'
            else request.args.get('template_id', '').strip()
        )
        catalog_entry = next(
            (entry for entry in _content_catalog(site, lang, default_lang) if entry.get('key') == dataset_key),
            None,
        )
        valid_template_ids = {
            str(tpl.get('id') or '') for tpl in (catalog_entry or {}).get('templates', [])
        }
        if not catalog_entry or template_id not in valid_template_ids:
            abort(400, '新建内容的分类或详情模板无效')
        if is_duplicate_content:
            duplicate_source = datasets.find(site.id, dataset_key, copy_from_id, lang=storage_lang)
            if not duplicate_source:
                abort(404, '副本来源内容不存在')
            item = copy.deepcopy(duplicate_source)
            item['id'] = 0
            item['template_id'] = template_id
            base_slug = str(duplicate_source.get('slug') or f'item-{copy_from_id}').strip()
            used_slugs = {
                str(existing.get('slug') or '')
                for existing in datasets.load(site.id, dataset_key, lang=storage_lang)
            }
            candidate = f'{base_slug}-copy'
            suffix = 2
            while candidate in used_slugs:
                candidate = f'{base_slug}-copy-{suffix}'
                suffix += 1
            title_key = (
                'title' if duplicate_source.get('title') is not None
                else ('name' if duplicate_source.get('name') is not None else 'title')
            )
            source_title = str(duplicate_source.get(title_key) or '未命名内容').strip()
            item['slug'] = candidate
            item[title_key] = f'{source_title} 副本'
        else:
            item = {
                'id': 0,
                'template_id': template_id,
                'date': datetime.now().date().isoformat(),
            }
        source_item = item
    else:
        item = datasets.find(site.id, dataset_key, item_id, lang=storage_lang)
        source_item = datasets.find(site.id, dataset_key, item_id, lang=source_storage_lang)
        if not item and storage_lang and source_item:
            item = source_item
        if not item:
            abort(404, f'数据不存在: {dataset_key}#{item_id}')
        source_item = source_item or item

    def render_edit(current_item, current_source_item=None):
        blocks = _get_available_blocks(site.template_name)
        slug = current_item.get('slug', '')
        settings = read_yaml(site.id, 'settings.yaml') or {}
        menu_items = settings.get('menu') or []
        is_list_page = any(
            mi.get('type') == 'list' and mi.get('target') == dataset_key
            for mi in menu_items
        )
        from app.core.menu import find_menu_path
        meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
        meta = _yaml.safe_load(meta_path.read_text(encoding='utf-8')) if meta_path.exists() else {}
        raw_menu = menu_lib.upgrade_old_format(menu_items, meta.get('datasets', []))
        preview_path = find_menu_path(raw_menu, dataset_key)
        page_label = next(
            (entry.get('label') for entry in menu_lib.collect_list_targets(raw_menu) if entry.get('target') == dataset_key),
            dataset_key,
        )
        page_cfg = _ensure_page_detail_templates(site.id, dataset_key, page_label)
        detail_templates = _detail_templates_for_page(page_cfg, dataset_key, page_label)
        default_template_id = _default_detail_template_id(page_cfg, dataset_key, page_label)
        # Primary media capabilities belong to the list module, not the
        # detail template. data_list_showcase can preview image/video/embed
        # directly in each row, while ordinary grids use a cover image only.
        list_page_configs = []
        checked_langs = set()
        for candidate_lang in [storage_lang, lang, default_lang] + [entry.get('code') for entry in languages]:
            if candidate_lang in checked_langs:
                continue
            checked_langs.add(candidate_lang)
            candidate_page = read_yaml(site.id, f'pages/{dataset_key}.yaml', default={}, lang=candidate_lang) or {}
            if isinstance(candidate_page, dict):
                list_page_configs.append(candidate_page)
        supports_rich_list_preview = any(
            isinstance(module, dict) and module.get('type') == 'data_list_showcase'
            for candidate_page in list_page_configs
            for module in (candidate_page.get('modules') or [])
        )
        # Field visibility in the dataset editor must follow the selected
        # detail template's components. Existing item data is preserved on
        # save, but it should not make every template show every legacy field.
        detail_requirements = _detail_template_requirements_map(detail_templates, current_item)
        selected_template_id = str(current_item.get('template_id') or default_template_id or '')
        selected_detail_template = next(
            (tpl for tpl in detail_templates if str(tpl.get('id') or '') == selected_template_id),
            detail_templates[0] if detail_templates else {},
        )
        auto_tags_mode = _detail_template_rule_value(selected_detail_template, 'auto_tags', 'suggest')
        auto_tags_preview = generated_technical_tags(current_item)
        detail_content_editor_blocks, detail_free_content_enabled = _detail_content_editor_state(
            selected_detail_template, current_item
        )
        all_list_datasets = menu_lib.collect_list_targets(menu_lib.normalize_for_render(raw_menu))
        from .style_registry import STYLE_REGISTRY
        from .icon_registry import icon_names
        template_name = 'dashboard/content_item_workspace.html' if workspace_mode else 'dashboard/panel_data_list.html'
        return _render(template_name,
                       user=user, site=site,
                       dataset_key=dataset_key, items=[current_item],
                       edit_prefix=f'_dataset/{dataset_key}',
                       edit_item=current_item, edit_item_id=item_id,
                       source_item=current_source_item or source_item,
                       current_lang=lang, languages=languages, default_lang=default_lang,
                       active=dataset_key,
                       blocks=blocks,
                       all_list_datasets=all_list_datasets,
                       is_list_page=is_list_page,
                       page_key=dataset_key,
                        preview_slug=slug,
                        preview_path=preview_path,
                        detail_templates=detail_templates,
                        default_template_id=default_template_id,
                        detail_requirements=detail_requirements,
                        detail_content_editor_blocks=detail_content_editor_blocks,
                        detail_free_content_enabled=detail_free_content_enabled,
                        auto_tags_mode=auto_tags_mode,
                        auto_tags_preview=auto_tags_preview,
                        supports_rich_list_preview=supports_rich_list_preview,
                        style_registry=STYLE_REGISTRY,
                        icon_list=icon_names(),
                        workspace_mode=workspace_mode,
                        is_new_content=is_new_content,
                        is_duplicate_content=is_duplicate_content,
                        copy_from_id=copy_from_id,
                        dataset_edit_endpoint=dataset_edit_endpoint,
                        page_label=page_label)

    if request.method == 'POST':
        if is_new_content:
            slug_value = request.form.get('slug', '').strip()
            title_value = request.form.get('title', '').strip()
            summary_value = request.form.get('summary', '').strip()
            media_type_value = request.form.get('media_type', 'image').strip() or 'image'
            media_fields = {
                'image': ('cover', 'cover_file', '封面图'),
                'video': ('video', 'video_file', '视频'),
                'embed': ('embed_url', 'embed_url_file', '嵌入页面'),
            }
            media_name, media_file_name, media_label = media_fields.get(
                media_type_value, media_fields['image']
            )
            media_upload = request.files.get(media_file_name)
            has_media = bool(
                request.form.get(media_name, '').strip()
                or (media_upload and media_upload.filename)
            )
            errors = []
            if not slug_value:
                errors.append('Slug')
            elif not re.fullmatch(r'[a-z0-9][a-z0-9-]{1,28}[a-z0-9]', slug_value):
                errors.append('Slug 格式')
            elif any(str(existing.get('slug') or '') == slug_value
                     for existing in datasets.load(site.id, dataset_key, lang=storage_lang)):
                errors.append('Slug 已存在')
            if not title_value:
                errors.append('标题')
            if not summary_value:
                errors.append('简介')
            if not has_media:
                errors.append(media_label)
            if errors:
                draft_item = dict(item)
                draft_item.update({key: value for key, value in request.form.items()
                                   if not key.startswith('_') and key != 'csrf_token'})
                flash('保存失败，请检查：' + '、'.join(errors), 'error')
                return render_edit(draft_item, draft_item), 400

        if storage_lang and not datasets.find(site.id, dataset_key, item_id, lang=storage_lang):
            source_items = datasets.load(site.id, dataset_key, lang=source_storage_lang)
            if source_items:
                datasets.save(site.id, dataset_key, source_items, lang=storage_lang)
        # 用旧数据做底，表单字段覆盖，避免种子字段（name/category/cover 等）被静默删除
        fields = {}
        for key, val in item.items():
            if key not in ('id', 'slug', 'modules', 'csrf_token') and not key.startswith('_draft_'):
                fields[key] = val
        for key in request.form:
            if key.startswith('_draft_'):
                continue
            if key.startswith('detail_gallery_') or key in ('detail_gallery_count',):
                continue
            if key == '_show_detail_btn_mode':
                continue
            if key in ('_advanced_modules_enabled', '_restore_template_modules'):
                continue
            if key.startswith('specs_') or key in ('specs_count',):
                continue
            if key.startswith('detail_specs_') or key in ('detail_specs_count',):
                continue
            if key.startswith('parameters_') or key in ('parameters_count',):
                continue
            if key.startswith('attributes_') or key in ('attributes_count',):
                continue
            if key.startswith('detail_action_'):
                continue
            if key.startswith('detail_links_') or key in ('detail_links_count',):
                continue
            if key.startswith('detail_tables_') or key in ('detail_tables_count',):
                continue
            if key.startswith('detail_features_') or key in ('detail_features_count',):
                continue
            if key.startswith('detail_files_') or key in ('detail_files_count',):
                continue
            if key.startswith('detail_faqs_') or key in ('detail_faqs_count',):
                continue
            if key.startswith('detail_content_blocks_') or key in ('detail_content_blocks_count',):
                continue
            # 跳过模块配置字段和 CSRF 令牌（不参与数据存储）
            if key.startswith('module_') or key.startswith('_') or key in ('module_count', 'csrf_token'):
                continue
            val = request.form.get(key, '').strip()
            fields[key] = val
        detail_btn_mode = request.form.get('_show_detail_btn_mode')
        if detail_btn_mode == 'inherit':
            fields.pop('show_detail_btn', None)
        elif detail_btn_mode in ('true', 'false'):
            fields['show_detail_btn'] = detail_btn_mode == 'true'
        # slug 唯一性校验
        new_slug = fields.get('slug', '').strip() or None
        if new_slug:
            # 格式校验: slug 会拼进详情页输出路径 {item_path}/{slug}/index.html,
            # 不校验则 `../../<任意路径>` 可让 builder 把 HTML 写到 output 目录外
            # (构建期任意文件写入)。复用站点级同一套 SLUG_PATTERN 严格白名单。
            if not SLUG_PATTERN.match(new_slug):
                flash(f'Slug "{new_slug}" 格式非法：只能用小写字母、数字、连字符，3-30 字符', 'error')
                invalid_item = dict(item)
                invalid_item.update(fields)
                return render_edit(invalid_item, source_item), 400
            all_items = datasets.load(site.id, dataset_key, lang=storage_lang)
            dup = next((it for it in all_items
                        if it.get('slug') == new_slug and it.get('id') != item_id), None)
            if dup:
                flash(f'Slug "{new_slug}" 已被 #{dup["id"]} 使用，请换一个', 'error')
                invalid_item = dict(item)
                invalid_item.update(fields)
                return render_edit(invalid_item, source_item), 400
        # tags: 逗号/空格分隔的字符串 → 列表
        if 'tags' in fields:
            fields['tags'] = _parse_tags_input(fields.get('tags'))
        # 处理图片上传
        if 'tags_visible' in fields:
            fields['tags_visible'] = str(fields.get('tags_visible')).lower() != 'false'
        if 'detail_gallery_count' in request.form or 'detail_gallery_visible' in request.form:
            gallery_count = 0
            try:
                gallery_count = int(request.form.get('detail_gallery_count', '0'))
            except (ValueError, TypeError):
                gallery_count = 0
            gallery_images = []
            for gi in range(gallery_count):
                url = request.form.get(f'detail_gallery_{gi}_url', '').strip()
                alt = request.form.get(f'detail_gallery_{gi}_url_alt', '').strip()
                upload = request.files.get(f'detail_gallery_{gi}_url_file')
                if upload and upload.filename:
                    try:
                        url = _save_uploaded_image(site.id, upload, prefix=f'{dataset_key}-detail-gallery-{gi + 1}')
                        alt = alt or _context_alt(fields, item, fallback=_filename_alt(upload))
                    except Exception as exc:
                        current_app.logger.warning('细节图库图片上传失败: %s', exc)
                if url:
                    alt = alt or _context_alt(fields, item)
                    image = {'url': url}
                    if alt:
                        image['alt'] = alt
                    gallery_images.append(image)
            fields['detail_gallery'] = {
                'visible': str(request.form.get('detail_gallery_visible', 'true')).lower() != 'false',
                'images': gallery_images,
            }
        for source_prefix in ('specs', 'parameters', 'attributes'):
            if f'{source_prefix}_count' in request.form:
                fields[source_prefix] = _parse_key_value_items_form(request.form, source_prefix)
        if 'detail_specs_count' in request.form:
            fields['detail_specs'] = _parse_detail_specs_form(request.form)
        if any(key.startswith('detail_action_') for key in request.form):
            fields['detail_actions'] = _parse_detail_actions_form(request.form)
        if 'detail_links_count' in request.form:
            links_count = 0
            try:
                links_count = int(request.form.get('detail_links_count', '0'))
            except (ValueError, TypeError):
                links_count = 0
            if links_count > 0:
                detail_links = []
                for li in range(links_count):
                    text = request.form.get(f'detail_links_{li}_text', '').strip()
                    url = request.form.get(f'detail_links_{li}_url', '').strip()
                    if text or url:
                        detail_links.append({'text': text, 'url': url})
                fields['detail_links'] = detail_links
                if detail_links:
                    fields['link_text'] = detail_links[0].get('text', '')
                    fields['link_url'] = detail_links[0].get('url', '')
        if 'detail_tables_count' in request.form:
            fields['detail_tables'] = _parse_detail_tables_form(request.form)
        if 'detail_features_count' in request.form:
            fields['detail_features'] = _parse_detail_features_form(request.form)
        if 'detail_files_count' in request.form:
            fields['detail_files'] = _parse_detail_files_form(request.form)
        if 'detail_faqs_count' in request.form:
            fields['detail_faqs'] = _parse_detail_faqs_form(request.form)
        if 'detail_content_blocks_count' in request.form:
            fields['detail_content_blocks'] = _parse_detail_content_blocks_form(
                request.form, request.files, site.id, dataset_key, fields, item
            )
        settings_for_templates = read_yaml(site.id, 'settings.yaml') or {}
        raw_menu_for_templates = settings_for_templates.get('menu') or []
        list_targets_for_templates = menu_lib.collect_list_targets(menu_lib.normalize_for_render(raw_menu_for_templates))
        page_label_for_templates = next(
            (entry.get('label') for entry in list_targets_for_templates if entry.get('target') == dataset_key),
            dataset_key,
        )
        page_cfg_for_templates = _ensure_page_detail_templates(site.id, dataset_key, page_label_for_templates)
        templates_for_autofill = _detail_templates_for_page(page_cfg_for_templates, dataset_key, page_label_for_templates)
        template_for_autofill = next(
            (tpl for tpl in templates_for_autofill if str(tpl.get('id') or '') == str(fields.get('template_id') or '')),
            None,
        )
        if template_for_autofill is None:
            default_template_id_for_autofill = _default_detail_template_id(page_cfg_for_templates, dataset_key, page_label_for_templates)
            template_for_autofill = next(
                (tpl for tpl in templates_for_autofill if str(tpl.get('id') or '') == str(default_template_id_for_autofill)),
                None,
            )
        _apply_detail_template_autofill(fields, template_for_autofill or {}, page_label_for_templates)
        for field_name in ('cover', 'image', 'photo', 'logo'):
            upload = request.files.get(field_name) or request.files.get(f'{field_name}_file')
            alt_key = _image_alt_key(field_name)
            if f'{field_name}_alt' in request.form or alt_key in request.form:
                fields[alt_key] = _form_alt_value(request.form, field_name, fields, item, existing=fields.get(alt_key))
            if upload and upload.filename:
                try:
                    fields[field_name] = _save_uploaded_image(site.id, upload, prefix=f'{dataset_key}-{field_name}')
                    fields[alt_key] = _form_alt_value(
                        request.form, field_name, fields, item,
                        upload=upload, existing=fields.get(alt_key)
                    )
                except Exception as exc:
                    current_app.logger.warning('数据集图片上传失败 %s: %s', field_name, exc)
            elif fields.get(field_name) and not str(fields.get(alt_key) or '').strip():
                fields[alt_key] = _context_alt(fields, item)
        video_upload = request.files.get('video_file')
        if video_upload and video_upload.filename:
            try:
                fields['video'] = _save_uploaded_media(site.id, video_upload, prefix=f'{dataset_key}-video')
            except Exception as exc:
                current_app.logger.warning('数据集视频上传失败: %s', exc)
        embed_upload = request.files.get('embed_url_file')
        if embed_upload and embed_upload.filename:
            try:
                result = _save_media_package(site.id, embed_upload)
                fields['embed_url'] = result.get('entry_url', '')
            except Exception as exc:
                current_app.logger.warning('数据集嵌入页面上传失败: %s', exc)
        # 保存模块配置到数据项 (item) 中
        # module_count 缺失表示表单不包含模块数据（例如用户未展开面板就保存），
        # 此时保留已有 modules 而非清空
        if request.form.get('_restore_template_modules') == '1':
            existing_modules = item.get('modules')
            if isinstance(existing_modules, list) and existing_modules:
                fields['modules_backup'] = copy.deepcopy(existing_modules)
            fields['modules'] = []
        module_count_str = request.form.get('module_count')
        if request.form.get('_restore_template_modules') != '1' and request.form.get('_advanced_modules_enabled') == '1' and module_count_str and module_count_str.isdigit():
            try:
                existing_modules = item.get('modules', [])
                modules = _parse_modules_form(request.form, existing_modules)
                # item_data：style 字段提升到 item 顶层；其余数据（images、specs 等）
                # 保留在模块 data 中，供 render_block 使用
                for m in modules:
                    if m.get('type') == 'item_data':
                        keep = {}
                        for key, value in (m.get('data') or {}).items():
                            if key.startswith('style_'):
                                fields[key] = value
                            else:
                                keep[key] = value
                        # 清理扁平残留键（已被 _parse_modules_form 结构化到
                        # images / specs 列表中），避免 YAML 冗余污染
                        for stale_prefix in ('images_', 'specs_'):
                            for k in list(keep.keys()):
                                if k.startswith(stale_prefix) and k not in ('images', 'specs'):
                                    keep.pop(k, None)
                        m['data'] = keep
                fields['modules'] = modules
            except Exception as exc:
                current_app.logger.warning('数据集编辑保存模块配置失败: %s', exc)
        elif request.form.get('_restore_template_modules') != '1' and request.form.get('_advanced_modules_enabled') == '1' and module_count_str is not None:
            # 明确传了 module_count 但非数字 → 清空
            fields['modules'] = []
        # 否则 module_count 不在表单中 → 保留旧 modules 不动

        if is_new_content:
            item_id = datasets.add(site.id, dataset_key, fields, lang=storage_lang)
            flash('内容已创建并保存')
        else:
            remove_fields = {'show_detail_btn'} if detail_btn_mode == 'inherit' else None
            datasets.update(
                site.id, dataset_key, item_id, fields,
                lang=storage_lang, remove_fields=remove_fields,
            )
            flash('已保存')
        # 保存后留在当前内容编辑器；统一列表入口已经迁移到“内容列表”。
        redirect_args = {'dataset_key': dataset_key, 'item_id': item_id, 'site': site.id, 'lang': lang}
        if not workspace_mode:
            redirect_args['_fragment'] = '1'
        return redirect(url_for(dataset_edit_endpoint, **redirect_args))

    return render_edit(item, source_item)

@bp.route('/_dataset/<path:dataset_key>/<int:item_id>/delete', methods=['POST'])
def dataset_delete(dataset_key, item_id):
    """通用数据集删除 — 支持 ?lang= 参数删除指定语言版本."""
    _validate_key(dataset_key)
    _, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    datasets.remove(site.id, dataset_key, item_id, lang=storage_lang)
    flash('已删除')
    return redirect(url_for('core.dataset_panel', dataset_key=dataset_key, _fragment='1', site=site.id, lang=lang))


@bp.route('/_dataset/<path:dataset_key>/<int:target_id>/paste-from/<int:source_id>', methods=['POST'])
def dataset_paste_from(dataset_key, target_id, source_id):
    """Copy one dataset item onto another, preserving the target id and slug."""
    _validate_key(dataset_key)
    _, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    items = datasets.load(site.id, dataset_key, lang=storage_lang)
    source = next((it for it in items if it.get('id') == source_id), None)
    target = next((it for it in items if it.get('id') == target_id), None)
    if not source or not target:
        return jsonify({'error': '数据不存在'}), 404
    new_item = copy.deepcopy(source)
    new_item['id'] = target.get('id')
    new_item['slug'] = target.get('slug')
    for i, item in enumerate(items):
        if item.get('id') == target_id:
            items[i] = new_item
            break
    datasets.save(site.id, dataset_key, items, lang=storage_lang)
    return jsonify({'ok': True})


@bp.route('/_panel/<path:page_key>', methods=['GET', 'POST'])
def page_panel(page_key):
    """动态菜单项面板路由：根据 page_key 分发到对应数据集列表或单页编辑.

    模块库是公用的——所有菜单页面都可以从同一个 blocks/ 中选择模块，
    只是每个页面填不同的数据，保存在 pages/<page_key>.yaml 的 modules 数组中。

    支持语言参数 ?lang=en 来编辑特定语言版本的页面内容。
    """
    _validate_key(page_key)
    user, site = _current_context()

    lang, languages, default_lang = _get_panel_lang(site)
    # 非默认语言时使用 lang 参数进行读写；默认语言读写根目录
    storage_lang = _storage_lang(site, lang, default_lang)
    source_storage_lang = _storage_lang(site, default_lang, default_lang)

    # POST：保存模块配置
    if request.method == 'POST':
        page = read_yaml(site.id, f'pages/{page_key}.yaml', lang=storage_lang) or {}
        existing_modules = page.get('modules', [])
        if storage_lang and not existing_modules:
            source_page_for_save = read_yaml(site.id, f'pages/{page_key}.yaml', lang=source_storage_lang) or {}
            existing_modules = source_page_for_save.get('modules', []) or existing_modules
        page['modules'] = _parse_modules_form(request.form, existing_modules)
        # 页面级 SEO 信息和模块配置共用同一个保存按钮；保存模块时不能把
        # title/description 清掉，否则健康检查引导填写后预览 head 仍然没有简介。
        if 'page_title' in request.form:
            title = request.form.get('page_title', '').strip()
            if title:
                page['title'] = title
            else:
                page.pop('title', None)
        if 'page_description' in request.form:
            description = request.form.get('page_description', '').strip()
            if description:
                page['description'] = description
            else:
                page.pop('description', None)
        write_yaml(site.id, f'pages/{page_key}.yaml', page, lang=storage_lang)
        flash('已保存')
        return redirect(url_for('core.page_panel', page_key=page_key, _fragment='1', site=site.id, lang=lang))

    # 判断 page_key 是否为 list 类型菜单
    settings = read_yaml(site.id, 'settings.yaml') or {}
    menu_items = settings.get('menu') or []
    if not menu_items:
        meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
        if meta_path.exists():
            template_meta = _yaml.safe_load(meta_path.read_text(encoding='utf-8')) or {}
            menu_items = template_meta.get('default_menu', [])

    def _find_list_in_menu(items, target_key):
        for item in (items or []):
            if item.get('type') == 'list' and item.get('target') == target_key:
                return True
            if item.get('children'):
                if _find_list_in_menu(item['children'], target_key):
                    return True
        return False

    is_list_page = _find_list_in_menu(menu_items, page_key)
    if is_list_page:
        # Ensure every list page has a default detail template. This only adds
        # missing config and never touches dataset items.
        _ensure_page_detail_templates(site.id, page_key)

    # 收集数据集列表，供数据网格模块选择数据源，也供模板 datasetNamesJson 序列化
    from app.core.menu import upgrade_old_format, normalize_for_render, ensure_home
    meta_path2 = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    meta2 = _yaml.safe_load(meta_path2.read_text(encoding='utf-8')) if meta_path2.exists() else {}
    datasets_meta = meta2.get('datasets', [])
    raw_menu = upgrade_old_format(menu_items, datasets_meta)
    normalized_menu = ensure_home(normalize_for_render(raw_menu))

    # 从菜单中查找 page_key 对应的实际显示名（如 home → 首页）
    def _find_page_label(items, target_key):
        for item in (items or []):
            # home 类型菜单项无 target 字段，通过 type == 'home' 匹配
            if item.get('target') == target_key or (target_key == 'home' and item.get('type') == 'home'):
                return item.get('label', target_key)
            if item.get('children'):
                found = _find_page_label(item['children'], target_key)
                if found:
                    return found
        return None
    page_display_name = _find_page_label(normalized_menu, page_key) or page_key

    all_list_datasets = menu_lib.collect_list_targets(normalized_menu)  # #22

    page = read_yaml(site.id, f'pages/{page_key}.yaml', lang=storage_lang)
    source_page = read_yaml(site.id, f'pages/{page_key}.yaml', lang=source_storage_lang) or {}
    if storage_lang and source_page.get('modules') and not (page or {}).get('modules'):
        page = copy.deepcopy(source_page)

    # 迁移：product_grid → data_grid（模块合并后的向后兼容）
    for _pg, _sl in [(page, storage_lang), (source_page, None)]:
        if _pg and _pg.get('modules'):
            _migrated = False
            for mod in _pg['modules']:
                if mod.get('type') == 'product_grid':
                    mod['type'] = 'data_grid'
                    _migrated = True
            if _migrated:
                write_yaml(site.id, f'pages/{page_key}.yaml', _pg, lang=_sl)

    if page:
        blocks = _get_available_blocks(site.template_name)
        is_modules_format = 'modules' in page
        page.setdefault('modules', [])
        _merge_block_defaults(page.get('modules'), blocks)
        from .style_registry import STYLE_REGISTRY
        from .icon_registry import icon_names
        return _render('dashboard/panel_page_edit.html',
                       user=user, site=site,
                       page_key=page_key, page_display_name=page_display_name,
                       page=page, blocks=blocks, is_modules_format=is_modules_format,
                       is_list_page=is_list_page,
                       all_list_datasets=all_list_datasets,
                       style_registry=STYLE_REGISTRY,
                       icon_list=icon_names(),
                       source_page=source_page,
                       current_lang=lang, languages=languages, default_lang=default_lang,
                       active=page_key)

    # 没有匹配任何已有内容：自动初始化
    new_page = {'modules': []}
    write_yaml(site.id, f'pages/{page_key}.yaml', new_page, lang=storage_lang)
    blocks = _get_available_blocks(site.template_name)
    _merge_block_defaults(new_page.get('modules'), blocks)
    from .style_registry import STYLE_REGISTRY
    from .icon_registry import icon_names
    return _render('dashboard/panel_page_edit.html',
                   user=user, site=site,
                   page_key=page_key, page_display_name=page_display_name,
                   page=new_page, blocks=blocks, is_modules_format=True,
                   is_list_page=is_list_page,
                   all_list_datasets=all_list_datasets,
                   style_registry=STYLE_REGISTRY,
                   icon_list=icon_names(),
                   source_page=source_page,
                   current_lang=lang, languages=languages, default_lang=default_lang,
                   active=page_key)


def _get_available_blocks(template_name):
    """获取模板的可用模块列表."""
    from .template_loader import scan_blocks
    try:
        blocks = scan_blocks(template_name)
        if template_name not in ('dengtec', 'claude'):
            blocks = [block for block in blocks if block.get('name') != 'contact_form']
        return blocks
    except Exception:
        return []


def _get_detail_template_components(template_name):
    """Components exposed in the detail-template editor.

    They are data-bound virtual components rendered by builder.py. Existing
    theme blocks may still be used internally as visual fallbacks, but the
    editor only exposes detail-specific concepts to keep the workflow focused.
    """
    return copy.deepcopy(DETAIL_TEMPLATE_COMPONENT_BLOCKS)


def _merge_block_defaults(modules, blocks):
    """将 meta.yaml 中非空 default 值合并到模块显示数据中（仅补全缺失的 key，不覆盖已有值）。
    这样属性面板的 Jinja2 模板用 mdata.get('key', '') 就能拿到 CSS 兜底值。
    """
    if not modules or not blocks:
        return
    # block name → {field_key: default_value}
    defaults_by_type = {}
    for b in blocks:
        field_defaults = {}
        for f in b.get('fields', []):
            d = f.get('default')
            if d is not None and d != '':
                field_defaults[f['key']] = d
        if field_defaults:
            defaults_by_type[b['name']] = field_defaults

    for m in modules:
        if not isinstance(m, dict):
            continue
        field_defaults = defaults_by_type.get(m.get('type', ''))
        if not field_defaults:
            continue
        data = m.get('data')
        if not isinstance(data, dict):
            continue
        for key, val in field_defaults.items():
            if key not in data:
                data[key] = val


def _parse_modules_form(form, existing_modules=None):
    """从 POST 表单解析 modules 数组（含 responsive 字段）.

    如果提供 existing_modules，表单未涉及的字段（如 items、features 等嵌套数组）
    会从已有数据中保留，防止编辑器保存时丢失表单不表达的数据。
    """
    data_field_allowed_types = {
        'columns': {'text_content', 'logo_cloud', 'detail_specs', 'detail_features', 'detail_related'},
        'max_items': {'data_grid', 'detail_related'},
        'items_per_page': {'data_grid'},
    }

    # 构建已有模块查找索引：(type, order) → existing_data
    # 注意：旧格式数据中 hero_banner 的 data 可能是直接列表（slides），
    # 需要包装为 dict 才能安全使用 .items()
    existing_by_key = {}
    if existing_modules:
        for em in existing_modules:
            if isinstance(em, dict) and em.get('type'):
                key = (em.get('type', ''), em.get('order', 0))
                raw_data = em.get('data', {})
                if isinstance(raw_data, dict):
                    existing_by_key[key] = raw_data
                elif isinstance(raw_data, list):
                    existing_by_key[key] = {'slides': raw_data}
                else:
                    existing_by_key[key] = {}

    def _parse_value(value):
        value = (value or '').strip()
        if not value:
            return ''
        # 保留布尔字符串原样，避免 yaml.safe_load 把 'true'/'false' 转成 Python bool
        # 否则模板中 == 'true' 的字符串比较会失败，导致分页等开关不生效
        if value.lower() in ('true', 'false', 'yes', 'no', 'on', 'off'):
            return value
        try:
            parsed = _yaml.safe_load(value)
        except _yaml.YAMLError:
            return value
        # 安全防护：若 yaml.safe_load 将值解析为 dict/list 等复合对象，
        # 说明原值恰好是合法 YAML 结构（如含冒号的多行文本），应保留原始字符串
        if isinstance(parsed, (dict, list)):
            return value
        return value if parsed is None else parsed

    count = 0
    try:
        count = int(form.get('module_count', '0'))
    except (ValueError, TypeError):
        pass

    # data-* 声明式 block 的 schema 表（按类型）：供下方通用 list/grid 条目解析。
    # 取不到（无站点上下文/扫描失败）则留空，回落到各 block 的硬编码解析分支。
    def _merge_meta_lists_into_schema(schema, meta_fields):
        if not isinstance(schema, dict):
            return schema
        merged = dict(schema)
        fields = list(merged.get('fields') or [])
        existing = set()

        def collect_field_names(items):
            for item in items or []:
                if not isinstance(item, dict):
                    continue
                name = item.get('name') or item.get('key')
                if name:
                    existing.add(name)
                collect_field_names(item.get('children') or item.get('item_fields') or [])

        collect_field_names(fields)
        for mf in meta_fields or []:
            if not isinstance(mf, dict):
                continue
            key = mf.get('key') or mf.get('name')
            if not key or key in existing or mf.get('type') not in ('list', 'grid'):
                continue
            item_fields = []
            for child in mf.get('item_fields') or mf.get('children') or []:
                if not isinstance(child, dict):
                    continue
                c = dict(child)
                c['name'] = c.get('name') or c.get('key') or ''
                if c['name']:
                    item_fields.append(c)
            fields.append({
                'name': key,
                'type': mf.get('type'),
                'label': mf.get('label') or key,
                'children': item_fields,
            })
            existing.add(key)
        merged['fields'] = fields
        return merged

    schema_by_type = {}
    try:
        _tpl_name = _current_context()[1].template_name
        for b in _get_available_blocks(_tpl_name):
            if b.get('is_data_attr') and b.get('schema') is not None:
                schema_by_type[b['name']] = _merge_meta_lists_into_schema(b['schema'], b.get('fields') or [])
    except Exception:
        current_app.logger.exception('_parse_modules_form: 构建 schema_by_type 失败，通用 list 解析将不生效——新添加的列表条目可能丢失')
        schema_by_type = {}

    modules = []
    for i in range(count):
        idx = f'module_{i}'
        m_type = form.get(f'{idx}_type', '').strip()
        if not m_type:
            continue
        variant = form.get(f'{idx}_variant', '').strip() or 'default'
        order_str = form.get(f'{idx}_order', str(i + 1))
        try:
            order = int(order_str)
        except (ValueError, TypeError):
            order = i + 1

        # 第一步：从表单构建 data，同时记录表单涉及的字段集合
        data = {}
        form_fields_for_module = set()  # 记录表单实际涉及的字段名（不含子字段后缀）
        for key in form:
            prefix = f'{idx}_data_'
            if key.startswith(prefix) and '_resp_' not in key:
                field = key[len(prefix):]
                if not any(k in key for k in ('_resp_tablet_', '_resp_mobile_', '_resp_columns', '_resp_max_items', '_resp_items_per_page')):
                    # 去掉子字段后缀（如 images_0_url → images）
                    base_field = field.split('_')[0] if '_' in field else field
                    form_fields_for_module.add(base_field)
                    form_fields_for_module.add(field)
                    data[field] = _parse_value(form.get(key, ''))


        # ===== 通用 data-* list/grid 条目解析 =====
        # 若该模块是 data-* 声明式且 schema 含 list/grid 字段，按 schema 通用还原：
        #   module_<i>_<listName>_count + module_<i>_<listName>_<j>_<subField>
        # → data[listName] = [{subField: val, ...}, ...]
        # 命中的 listName 记入 handled_lists，跳过后面对应的硬编码分支（避免重复解析）。
        # 现有模块走旧 Jinja2 编辑器用单数命名（feature_count 等），count_key 不存在 →
        # 不命中，仍由硬编码分支处理，两套互不干扰。
        handled_lists = set()
        _schema = schema_by_type.get(m_type)
        if _schema is not None:
            # 递归遍历所有字段（穿透 group 的 children），确保嵌套 list/grid 也能被解析
            def _schema_children(field):
                children = field.get('children') or field.get('item_fields') or []
                normalized = []
                for child in children:
                    if not isinstance(child, dict):
                        continue
                    c = dict(child)
                    c['name'] = c.get('name') or c.get('key') or ''
                    if c.get('name'):
                        normalized.append(c)
                return normalized

            def _iter_list_fields(fields):
                for f in fields:
                    if f.get('type', '') in ('list', 'grid'):
                        yield f
                    children = _schema_children(f)
                    if children:
                        yield from _iter_list_fields(children)

            for lf in _iter_list_fields(_schema.get('fields', [])):
                list_name = lf.get('name', '')
                # 兼容两种表单 key 格式:
                #   schema 表单 → module_0_images_count（无 _data_）
                #   admin_modules.js 硬编码 → module_0_data_images_count（有 _data_）
                count_key = f'{idx}_{list_name}_count'
                alt_count_key = f'{idx}_data_{list_name}_count'
                is_alt_fmt = False
                if count_key not in form:
                    if alt_count_key in form:
                        count_key = alt_count_key
                        is_alt_fmt = True
                    else:
                        continue  # 表单未表达该 list
                try:
                    item_n = int(form.get(count_key, '0') or '0')
                except (ValueError, TypeError):
                    item_n = 0
                # 子字段名 + 类型 + data-href 字段名
                sub_specs = [(c.get('name', ''), c.get('type', ''), c.get('href_field', '')) for c in _schema_children(lf)]
                items = []
                for j in range(item_n):
                    item_prefix = f'{idx}_data_{list_name}_{j}_' if is_alt_fmt else f'{idx}_{list_name}_{j}_'
                    entry = {}
                    for sub_name, sub_type, href_field in sub_specs:
                        # 图片/视频/网页包字段：优先处理文件上传，否则取 URL 文本值
                        if sub_type in ('image', 'video', 'embed'):
                            upload = request.files.get(f'{item_prefix}{sub_name}_file')
                            if upload and upload.filename:
                                try:
                                    if sub_type == 'embed':
                                        # 网页包：zip → 解压为可嵌入页面
                                        result = _save_media_package(
                                            _current_context()[1].id, upload
                                        )
                                        val = result.get('entry_url', '')
                                    else:
                                        val = _save_uploaded_media(
                                            _current_context()[1].id, upload,
                                            prefix=f'{m_type}-{sub_name}-{j + 1}'
                                        )
                                        alt_val = form.get(f'{item_prefix}{sub_name}_alt', '').strip()
                                        if not alt_val:
                                            alt_val = _context_alt(data, fallback=_filename_alt(upload))
                                        if alt_val:
                                            entry[_image_alt_key(sub_name)] = alt_val
                                except Exception as exc:
                                    current_app.logger.warning('上传失败: %s', exc)
                                    val = _parse_value(form.get(f'{item_prefix}{sub_name}', ''))
                            else:
                                val = _parse_value(form.get(f'{item_prefix}{sub_name}', ''))
                                alt_val = form.get(f'{item_prefix}{sub_name}_alt', '').strip()
                                if alt_val:
                                    entry[_image_alt_key(sub_name)] = alt_val
                        else:
                            val = _parse_value(form.get(f'{item_prefix}{sub_name}', ''))
                        if val not in (None, ''):
                            entry[sub_name] = val
                            if sub_type == 'image' and not any(entry.get(k) for k in ('alt', _image_alt_key(sub_name))):
                                auto_alt = _context_alt(data)
                                if auto_alt:
                                    entry[_image_alt_key(sub_name)] = auto_alt
                        if href_field:
                            hval = _parse_value(form.get(f'{item_prefix}{href_field}', ''))
                            if hval not in (None, ''):
                                entry[href_field] = hval
                    if entry:  # 跳过完全空白的条目
                        items.append(entry)
                data[list_name] = items
                form_fields_for_module.add(list_name)  # 表单已表达该列表；空列表也要覆盖旧数据
                handled_lists.add(list_name)

        # 通用 data-* 顶层 image/video/embed 字段：处理文件上传（list 内字段已在上面处理）
        if _schema is not None:
            for lf in _schema.get('fields', []):
                if lf.get('type', '') in ('list', 'grid', 'group'):
                    continue
                if lf.get('type', '') not in ('image', 'video', 'embed'):
                    continue
                field_name = lf.get('name', '')
                alt_key = _image_alt_key(field_name)
                if f'{idx}_data_{field_name}_alt' in form:
                    alt_val = form.get(f'{idx}_data_{field_name}_alt', '').strip()
                    if alt_val:
                        data[alt_key] = alt_val
                upload = request.files.get(f'{idx}_data_{field_name}_file')
                if upload and upload.filename:
                    try:
                        if lf.get('type', '') == 'embed':
                            # 网页包：zip → 解压为可嵌入页面
                            result = _save_media_package(
                                _current_context()[1].id, upload
                            )
                            data[field_name] = result.get('entry_url', '')
                        else:
                            data[field_name] = _save_uploaded_media(
                                _current_context()[1].id, upload,
                                prefix=f'{m_type}-{field_name}'
                            )
                            data[alt_key] = _form_alt_value(
                                form, f'{idx}_data_{field_name}',
                                data, upload=upload, existing=data.get(alt_key)
                            )
                    except Exception as exc:
                        current_app.logger.warning('上传失败 %s: %s', field_name, exc)

            style_tokens = list(_schema.get('style_tokens', []) or [])
            for token in _schema.get('element_style_tokens', []) or []:
                if token not in style_tokens:
                    style_tokens.append(token)
            for token in style_tokens:
                sdef = style_registry.get_style_def(token)
                if not sdef or sdef.get('control') != 'image':
                    continue
                upload = request.files.get(f'{idx}_data_style_{token}_file')
                if upload and upload.filename:
                    try:
                        data[f'style_{token}'] = _save_uploaded_media(
                            _current_context()[1].id, upload,
                            prefix=f'{m_type}-style-{token}'
                        )
                    except Exception as exc:
                        current_app.logger.warning('样式图片上传失败 %s: %s', token, exc)

        if m_type == 'hero_banner':
            slide_count = 0
            try:
                slide_count = int(form.get(f'{idx}_slide_count', '0'))
            except (ValueError, TypeError):
                slide_count = 0

            slides = []
            for slide_i in range(slide_count):
                slide_prefix = f'{idx}_slide_{slide_i}_'
                slide = {}
                for field in (
                    'type', 'media', 'title', 'subtitle', 'badge',
                    'primaryBtn', 'primaryBtnLink', 'primaryBtnLinkTarget',
                    'secondaryBtn', 'secondaryBtnLink',
                    'cta_text', 'cta_url', 'video_url', 'background_image'
                ):
                    value = form.get(f'{slide_prefix}{field}', '').strip()
                    if value:
                        slide[field] = _parse_value(value)

                upload = request.files.get(f'{slide_prefix}file')
                if upload and upload.filename:
                    media_url = _save_uploaded_media(
                        _current_context()[1].id,
                        upload,
                        prefix=f'{m_type}-slide-{slide_i + 1}',
                    )
                    suffix = upload.filename.rsplit('.', 1)[-1].lower() if '.' in upload.filename else ''
                    slide['type'] = 'video' if suffix in ALLOWED_VIDEO_EXTENSIONS else 'image'
                    slide['media'] = media_url
                    if slide['type'] == 'image':
                        slide['alt'] = _context_alt(slide, data, fallback=_filename_alt(upload))

                if slide.get('media') or slide.get('title') or slide.get('subtitle'):
                    slides.append(slide)

            if slides:
                data['slides'] = slides
            else:
                slides_value = data.get('slides')
                if isinstance(slides_value, list):
                    data['slides'] = slides_value
                elif isinstance(slides_value, str) and slides_value.strip():
                    parsed_slides = _parse_value(slides_value)
                    if isinstance(parsed_slides, list):
                        data['slides'] = parsed_slides

            uploaded_slides = []
            for upload in request.files.getlist(f'{idx}_data_slides_files'):
                if upload and upload.filename:
                    media_url = _save_uploaded_media(
                        _current_context()[1].id,
                        upload,
                        prefix=f'{m_type}-slide',
                    )
                    suffix = upload.filename.rsplit('.', 1)[-1].lower() if '.' in upload.filename else ''
                    uploaded_slides.append({
                        'type': 'video' if suffix in ALLOWED_VIDEO_EXTENSIONS else 'image',
                        'media': media_url,
                        'title': data.get('title', ''),
                        'subtitle': data.get('subtitle', ''),
                        'primaryBtn': data.get('primaryBtn') or data.get('cta_text', ''),
                        'primaryBtnLink': data.get('primaryBtnLink') or data.get('cta_url', ''),
                        'cta_text': data.get('cta_text', ''),
                        'cta_url': data.get('cta_url', ''),
                        'badge': data.get('badge', ''),
                    })
                    if uploaded_slides[-1]['type'] == 'image':
                        uploaded_slides[-1]['alt'] = _context_alt(data, fallback=_filename_alt(upload))
            if uploaded_slides:
                existing = data.get('slides') if isinstance(data.get('slides'), list) else []
                data['slides'] = existing + uploaded_slides

        if m_type == 'item_detail':
            # data-* schema 表单（_schemaListEditor）已走通用 list 解析，
            # 这里仅作旧 Jinja2 / admin_modules.js 表单的兜底（handled_lists 守卫）。
            if 'images' not in handled_lists:
                images_count = 0
                try:
                    images_count = int(form.get(f'{idx}_data_images_count', '0'))
                except (ValueError, TypeError):
                    pass
                images = []
                for ii in range(images_count):
                    url = form.get(f'{idx}_data_images_{ii}_url', '').strip()
                    alt = form.get(f'{idx}_data_images_{ii}_url_alt', '').strip()
                    upload = request.files.get(f'{idx}_data_images_{ii}_url_file')
                    if upload and upload.filename:
                        try:
                            url = _save_uploaded_image(
                                _current_context()[1].id, upload,
                                prefix=f'{m_type}-img-{ii + 1}'
                            )
                            alt = alt or _context_alt(data, fallback=_filename_alt(upload))
                        except Exception as exc:
                            current_app.logger.warning('模块图片上传失败: %s', exc)
                if url:
                    alt = alt or _context_alt(data)
                    image = {'url': url}
                    if alt:
                        image['alt'] = alt
                        images.append(image)
                if images:
                    data['images'] = images
                else:
                    data.pop('images', None)

            if 'specs' not in handled_lists:
                specs_count = 0
                try:
                    specs_count = int(form.get(f'{idx}_data_specs_count', '0'))
                except (ValueError, TypeError):
                    pass
                specs = []
                for si in range(specs_count):
                    name = form.get(f'{idx}_data_specs_{si}_name', '').strip()
                    value = form.get(f'{idx}_data_specs_{si}_value', '').strip()
                    if name or value:
                        specs.append({'name': name, 'value': value})
                if specs:
                    data['specs'] = specs
                else:
                    data.pop('specs', None)

        if m_type == 'item_data':
            # item_data 的 images / specs 表单字段命名与 item_detail 完全一致
            # （admin_modules.js 硬编码编辑器使用相同前缀 module_X_data_images_Y_url）,
            # 这里复用相同的解析逻辑，确保不依赖 schema_by_type 的通用解析路径
            if 'images' not in handled_lists:
                images_count = 0
                try:
                    images_count = int(form.get(f'{idx}_data_images_count', '0'))
                except (ValueError, TypeError):
                    pass
                images = []
                for ii in range(images_count):
                    url = form.get(f'{idx}_data_images_{ii}_url', '').strip()
                    upload = request.files.get(f'{idx}_data_images_{ii}_url_file')
                    if upload and upload.filename:
                        try:
                            url = _save_uploaded_image(
                                _current_context()[1].id, upload,
                                prefix=f'{m_type}-img-{ii + 1}'
                            )
                        except Exception as exc:
                            current_app.logger.warning('item_data 图片上传失败: %s', exc)
                    if url:
                        images.append({'url': url})
                if images:
                    data['images'] = images
                else:
                    data.pop('images', None)

            if 'specs' not in handled_lists:
                specs_count = 0
                try:
                    specs_count = int(form.get(f'{idx}_data_specs_count', '0'))
                except (ValueError, TypeError):
                    pass
                specs = []
                for si in range(specs_count):
                    name = form.get(f'{idx}_data_specs_{si}_name', '').strip()
                    value = form.get(f'{idx}_data_specs_{si}_value', '').strip()
                    if name or value:
                        specs.append({'name': name, 'value': value})
                if specs:
                    data['specs'] = specs
                else:
                    data.pop('specs', None)

        if m_type == 'feature_grid' and 'features' not in handled_lists:
            feature_count = 0
            try:
                feature_count = int(form.get(f'{idx}_features_count', '0'))
            except (ValueError, TypeError):
                feature_count = 0

            features = []
            for fi in range(feature_count):
                prefix = f'{idx}_features_{fi}_'
                item = {}
                for field in ('icon', 'title', 'desc'):
                    value = form.get(f'{prefix}{field}', '').strip()
                    if value:
                        item[field] = value
                if item.get('title') or item.get('desc') or item.get('icon'):
                    features.append(item)

            if features:
                data['features'] = features
            else:
                features_value = data.get('features')
                if isinstance(features_value, list):
                    data['features'] = features_value
                elif isinstance(features_value, str) and features_value.strip():
                    parsed_features = _parse_value(features_value)
                    if isinstance(parsed_features, list):
                        data['features'] = parsed_features

        # 解析 stat_counter 的统计项列表
        if m_type == 'stat_counter' and 'stats' not in handled_lists:
            stat_count = 0
            try:
                stat_count = int(form.get(f'{idx}_stats_count', '0'))
            except (ValueError, TypeError):
                stat_count = 0
            stats = []
            for si in range(stat_count):
                prefix = f'{idx}_stats_{si}_'
                item = {}
                for field in ('icon', 'number', 'suffix', 'label'):
                    value = form.get(f'{prefix}{field}', '').strip()
                    if value:
                        item[field] = value
                if item.get('label') or item.get('number'):
                    stats.append(item)
            if stats:
                data['stats'] = stats

        # 解析 logo_cloud 的 Logo 列表
        if m_type == 'logo_cloud' and 'logos' not in handled_lists:
            logo_count = 0
            try:
                logo_count = int(form.get(f'{idx}_logos_count', '0'))
            except (ValueError, TypeError):
                logo_count = 0
            logos = []
            for li in range(logo_count):
                prefix = f'{idx}_logos_{li}_'
                item = {}
                # 键名对齐 data-* 模板：图片存 logo、链接存 link（renderer 读这两个 key）
                for field in ('logo', 'link'):
                    value = form.get(f'{prefix}{field}', '').strip()
                    if value:
                        item[field] = value
                upload = request.files.get(f'{prefix}logo_file')
                if upload and upload.filename:
                    try:
                        item['logo'] = _save_uploaded_image(
                            _current_context()[1].id,
                            upload,
                            prefix=f'logo-{li + 1}',
                        )
                    except Exception as exc:
                        current_app.logger.warning('Logo 图片上传失败: %s', exc)
                if item.get('logo'):
                    logos.append(item)
            if logos:
                data['logos'] = logos

        # 解析 process_steps 的步骤列表
        if m_type == 'process_steps' and 'steps' not in handled_lists:
            step_count = 0
            try:
                step_count = int(form.get(f'{idx}_step_count', '0'))
            except (ValueError, TypeError):
                step_count = 0
            steps = []
            for si in range(step_count):
                prefix = f'{idx}_step_{si}_'
                item = {}
                for field in ('title', 'desc', 'icon'):
                    value = form.get(f'{prefix}{field}', '').strip()
                    if value:
                        item[field] = value
                if item.get('title') or item.get('desc'):
                    steps.append(item)
            if steps:
                data['steps'] = steps


        # 处理模块顶层图片字段：扫描 data 中所有字段，找到图片字段（image/cover 等），
        # 从 request.files 中取对应 _file 后缀的文件。跳过 _convert_webp 等辅助字段。
        # 注意：data 里可能混入了 image_file（文件输入框的值）和 image_convert_webp
        # （勾选框值），需要按后缀精确过滤，避免误把文件名或 'true' 当作图片 URL。
        for field in list(data.keys()):
            # 跳过文件输入框值和 WebP 转换标记——它们不是图片 URL
            if field.endswith('_file') or field.endswith('_convert_webp'):
                continue
            if _field_looks_like_image(field):
                alt_key = _image_alt_key(field)
                alt_form_key = f'{idx}_data_{field}_alt'
                if alt_form_key in form and form.get(alt_form_key, '').strip():
                    data[alt_key] = form.get(alt_form_key, '').strip()
                upload = request.files.get(f'{idx}_data_{field}_file')
                if upload and upload.filename:
                    try:
                        data[field] = _save_uploaded_image(
                            _current_context()[1].id,
                            upload,
                            prefix=f'{m_type}-{field}',
                        )
                        data[alt_key] = _form_alt_value(
                            form, f'{idx}_data_{field}',
                            data, upload=upload, existing=data.get(alt_key)
                        )
                    except Exception as exc:
                        current_app.logger.warning('模块图片保存失败 %s: %s', field, exc)
                if data.get(field) and not str(data.get(alt_key) or '').strip():
                    auto_alt = _context_alt(data)
                    if auto_alt:
                        data[alt_key] = auto_alt

        # 兼容旧表单：仅模块自身真正支持时才接收这些顶层字段
        columns_val = form.get(f'{idx}_resp_columns', '').strip()
        if columns_val and m_type in data_field_allowed_types['columns']:
            try:
                data['columns'] = int(columns_val)
            except ValueError:
                pass
        max_items_val = form.get(f'{idx}_resp_max_items', '').strip()
        if max_items_val and m_type in data_field_allowed_types['max_items']:
            try:
                data['max_items'] = int(max_items_val)
            except ValueError:
                pass
        items_per_page_val = form.get(f'{idx}_resp_items_per_page', '').strip()
        if items_per_page_val and m_type in data_field_allowed_types['items_per_page']:
            try:
                data['items_per_page'] = int(items_per_page_val)
            except ValueError:
                pass

        # 解析响应式配置
        responsive = {}
        for device in ('tablet', 'mobile'):
            device_data = {}
            # 设备独立数据字段
            for key in form:
                prefix = f'{idx}_resp_{device}_data_'
                if key.startswith(prefix):
                    field = key[len(prefix):]
                    val = form.get(key, '').strip()
                    if val:
                        device_data[field] = _parse_value(val)

            # 设备 hidden
            if form.get(f'{idx}_resp_{device}_hidden'):
                device_data['hidden'] = True

            if device_data:
                responsive[device] = device_data

        # 第二步：从已有数据中保留表单未涉及的字段（防止嵌套数组丢失）
        existing_key = (m_type, order)
        if existing_key in existing_by_key and isinstance(existing_by_key[existing_key], dict):
            for ek, ev in existing_by_key[existing_key].items():
                if ek not in form_fields_for_module and ek not in data:
                    data[ek] = ev
                elif ek in form_fields_for_module and ek not in data:
                    # 表单表达了该字段（如 images_count）但解析后 data 中没有该 key
                    # （如图片列表为空未设置 data['images']）→ 从旧数据恢复
                    data[ek] = ev

        if m_type == 'stat_counter' and data.get('columns') and not data.get('style_cols'):
            data['style_cols'] = str(data.get('columns'))

        for stale_field, allowed_types in data_field_allowed_types.items():
            if m_type not in allowed_types:
                data.pop(stale_field, None)
        for device_data in responsive.values():
            for stale_field in data_field_allowed_types:
                device_data.pop(stale_field, None)
        responsive = {device: cfg for device, cfg in responsive.items() if cfg}

        module = {
            'type': m_type,
            'order': order,
            'variant': variant,
            'data': data,
        }
        if responsive:
            module['responsive'] = responsive

        modules.append(module)

    return modules
