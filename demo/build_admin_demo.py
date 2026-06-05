"""生成独立 HTML 演示文件 — 后台三栏布局 + 预览标签栏 + 首页模块编辑器。"""
from pathlib import Path

HERE = Path(__file__).parent
ADMIN_CSS = Path(r"f:\dengtec\mycompany.website11\app\static\css\admin.css")

CSS = ADMIN_CSS.read_text(encoding="utf-8")

HTML = rf'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>演示站点 — mycompany.website</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css">
<style>
/* ===== 内联 admin.css ===== */
{CSS}

/* ===== 预览标签栏 ===== */
.preview-tab-bar {{
  display: flex; align-items: center; gap: 0; background: #f1f5f9; border-bottom: 1px solid #e2e8f0;
  padding: 0 8px; overflow-x: auto; flex-shrink: 0; min-height: 36px;
}}
.preview-tab {{
  display: flex; align-items: center; gap: 6px; padding: 6px 10px 6px 12px;
  font-size: 12px; color: #64748b; background: #e2e8f0; border-radius: 8px 8px 0 0;
  cursor: pointer; white-space: nowrap; transition: all .12s; margin-top: 4px;
  border: 1px solid transparent; border-bottom: none; position: relative;
}}
.preview-tab:hover {{ color: #334155; background: #cbd5e1; }}
.preview-tab.active {{ color: #1e293b; background: #fff; border-color: #e2e8f0; font-weight: 500; }}
.preview-tab .tab-favicon {{ width: 14px; height: 14px; border-radius: 2px; flex-shrink: 0; background: #94a3b8; }}
.preview-tab .tab-close {{
  display: inline-flex; align-items: center; justify-content: center; width: 16px; height: 16px;
  border-radius: 50%; border: none; background: transparent; color: #94a3b8;
  font-size: 14px; line-height: 1; cursor: pointer; padding: 0; transition: all .12s;
}}
.preview-tab .tab-close:hover {{ background: rgba(0,0,0,.1); color: #334155; }}
.preview-tab-add {{
  display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px;
  border-radius: 50%; border: none; background: transparent; color: #64748b;
  font-size: 16px; line-height: 1; cursor: pointer; padding: 0; flex-shrink: 0; margin-left: 4px; margin-top: 4px;
}}
.preview-tab-add:hover {{ background: #e2e8f0; color: #1e293b; }}

/* ===== URL 栏 ===== */
.preview-url-bar {{
  display: flex; align-items: center; gap: 8px; padding: 6px 12px; background: #fff;
  border-bottom: 1px solid #e2e8f0; font-size: 12px; color: #94a3b8; flex-shrink: 0;
}}
.preview-url-bar .url-icon {{ width: 14px; height: 14px; flex-shrink: 0; color: #22c55e; }}
.preview-url-bar .url-text {{ font-family: var(--font-family-mono, monospace); color: #475569; }}

/* ===== 页面选择器模态框 ===== */
.page-tree-modal .modal-body {{ max-height: 60vh; overflow-y: auto; }}
.page-tree-search {{ margin-bottom: 12px; }}
.page-tree-item {{
  display: flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 6px;
  cursor: pointer; transition: background .12s; font-size: 13px; color: #334155;
}}
.page-tree-item:hover {{ background: #f1f5f9; }}
.page-tree-item.highlighted {{ background: rgba(6,122,122,.1); color: #067a7a; font-weight: 500; }}
.page-tree-item .page-tree-icon {{ width: 18px; height: 18px; flex-shrink: 0; color: #94a3b8; }}
.page-tree-category {{
  font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase;
  letter-spacing: .05em; padding: 6px 12px 2px;
}}
.page-tree-child {{ padding-left: 32px !important; font-size: 12px; }}
.page-tree-empty {{ padding: 20px; text-align: center; color: #94a3b8; font-size: 13px; }}

/* ===== 内联 iframe 演示页 ===== */
.demo-preview-page {{
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Noto Sans SC', sans-serif;
  padding: 40px 20px; max-width: 960px; margin: 0 auto; color: #1e293b;
}}
.demo-preview-page h1 {{ font-size: 2rem; margin-bottom: 8px; }}
.demo-preview-page p {{ color: #64748b; margin-bottom: 24px; }}
.demo-preview-card {{
  background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 20px;
  margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,.04);
}}
</style>
</head>
<body class="d-flex flex-column vh-100">

<!-- ====== 顶栏 ====== -->
<header class="admin-header">
  <div class="d-flex align-items-center h-100 px-3 gap-2">
    <a href="#" class="d-flex align-items-center gap-2 text-decoration-none">
      <svg class="admin-logo" width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect width="28" height="28" rx="6" fill="#067a7a"/>
        <rect x="5" y="7" width="7" height="5" rx="1.5" fill="#fff" opacity="0.95"/>
        <rect x="16" y="7" width="7" height="5" rx="1.5" fill="#fff" opacity="0.95"/>
        <rect x="5" y="16" width="7" height="5" rx="1.5" fill="#fff" opacity="0.95"/>
        <rect x="16" y="16" width="7" height="5" rx="1.5" fill="#fff" opacity="0.95"/>
      </svg>
      <span class="admin-brand">mycompany.website</span>
    </a>

    <div class="header-divider"></div>

    <div class="dropdown">
      <button class="header-btn header-site-btn dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false">
        演示站点
      </button>
      <ul class="dropdown-menu">
        <li><a class="dropdown-item active" href="#">演示站点 <span class="text-muted small">/demo</span></a></li>
        <li><a class="dropdown-item" href="#">另一个站点 <span class="text-muted small">/other</span></a></li>
      </ul>
    </div>

    <a class="header-btn" href="javascript:void(0)" onclick="demoToast('模板库')">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
      新建站点
    </a>

    <div class="flex-grow-1"></div>

    <a class="header-btn" href="#" onclick="demoToast('预览')" title="在新窗口中打开站点预览">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
      预览
    </a>
    <a class="header-btn" href="#" onclick="demoToast('导出')">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
      导出
    </a>
    <a class="header-btn header-btn-primary" href="javascript:demoToast('发布')">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>
      发布
    </a>

    <div class="header-divider"></div>

    <button class="header-btn" type="button" onclick="demoToast('已退出')">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
      退出
    </button>

    <div class="admin-avatar" title="demo@example.com">D</div>
  </div>
</header>

<!-- ====== 三栏主体 ====== -->
<div class="d-flex flex-grow-1 overflow-hidden position-relative">

  <!-- ====== 左栏：导航 ====== -->
  <nav class="flex-shrink-0 overflow-auto" id="leftNav">
    <div class="left-nav-site-info px-3 py-2">
      <div class="site-label">我的网站</div>
      <div class="site-name">演示站点</div>
    </div>

    <div class="d-flex flex-column">
      <div class="left-nav-section-title">设置</div>
      <a class="left-nav-item" href="#" data-panel="company" title="公司信息" onclick="switchLeftNav(event, this, 'companyPanel')">
        <svg class="left-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
        公司信息
      </a>
      <a class="left-nav-item" href="#" data-panel="header" title="网站头部" onclick="switchLeftNav(event, this, 'headerPanel')">
        <svg class="left-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="8" rx="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="10" y1="6" x2="10.01" y2="6"/><line x1="14" y1="6" x2="14.01" y2="6"/></svg>
        网站头部
      </a>
      <a class="left-nav-item" href="#" data-panel="menu" title="菜单配置" onclick="switchLeftNav(event, this, 'menuPanel')">
        <svg class="left-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
        菜单配置
      </a>
      <a class="left-nav-item" href="#" data-panel="footer_variant" title="网站底部" onclick="switchLeftNav(event, this, 'footerPanel')">
        <svg class="left-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="16" width="20" height="6" rx="2"/><line x1="6" y1="18" x2="6.01" y2="18"/><line x1="10" y1="18" x2="10.01" y2="18"/></svg>
        网站底部
      </a>
      <a class="left-nav-item" href="#" data-panel="theme" title="主题颜色" onclick="switchLeftNav(event, this, 'themePanel')">
        <svg class="left-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a10 10 0 0 1 0 20"/><path d="M2 12h20"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10"/><path d="M12 2a15.3 15.3 0 0 0-4 10 15.3 15.3 0 0 0 4 10"/></svg>
        主题颜色
      </a>
      <a class="left-nav-item" href="#" data-panel="account" title="账号管理" onclick="switchLeftNav(event, this, 'accountPanel')">
        <svg class="left-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
        账号管理
      </a>

      <div class="left-nav-section-title">内容</div>
      <a class="left-nav-item active" href="#" data-panel="overview" title="总览" onclick="switchLeftNav(event, this, 'overviewPanel')">
        <svg class="left-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
        总览
      </a>
      <a class="left-nav-item" href="#" data-panel="pages_home" data-preview-page="home" title="首页" onclick="switchLeftNav(event, this, 'homePanel'); openPreviewTab('home', '🏠 首页', 'https://demo.mycompany.website/')">
        <svg class="left-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
        首页
      </a>

      <!-- 菜单: 产品列表 (有子菜单) -->
      <div class="left-nav-group" data-level="0">
        <div class="left-nav-parent-row">
          <a class="left-nav-item left-nav-parent-link flex-grow-1" href="#" data-panel="list_products" data-preview-page="products" title="产品列表" onclick="switchLeftNav(event, this, 'listPanel'); openPreviewTab('products', '📋 产品列表', 'https://demo.mycompany.website/products/')">
            <svg class="left-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
            产品列表
            <span class="nav-badge">12</span>
          </a>
          <button class="left-nav-chevron-btn" type="button" onclick="toggleLeftSubmenu(this)" title="展开/折叠子菜单">
            <svg class="left-nav-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M9 18l6-6-6-6"/>
            </svg>
          </button>
        </div>
        <div class="left-nav-submenu" style="display:none">
          <a class="left-nav-item" href="#" style="padding-left:32px" data-preview-page="product-detail" title="静音舱-3000" onclick="switchLeftNav(event, this, ''); openPreviewTab('product-sb3000', '🏷 静音舱-3000', 'https://demo.mycompany.website/products/silent-booth-3000/')">
            <svg class="left-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            静音舱-3000
          </a>
          <a class="left-nav-item" href="#" style="padding-left:32px" data-preview-page="product-detail" title="静音舱-5000" onclick="switchLeftNav(event, this, ''); openPreviewTab('product-sb5000', '🏷 静音舱-5000', 'https://demo.mycompany.website/products/silent-booth-5000/')">
            <svg class="left-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            静音舱-5000
          </a>
        </div>
      </div>

      <!-- 菜单: 关于我们 -->
      <a class="left-nav-item" href="#" data-panel="page_about" data-preview-page="about" title="关于我们" onclick="switchLeftNav(event, this, 'pagePanel'); openPreviewTab('about', '📄 关于我们', 'https://demo.mycompany.website/about/')">
        <svg class="left-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
        关于我们
      </a>

      <!-- 菜单: 文章列表 (有子菜单) -->
      <div class="left-nav-group" data-level="0">
        <div class="left-nav-parent-row">
          <a class="left-nav-item left-nav-parent-link flex-grow-1" href="#" data-panel="list_posts" data-preview-page="posts" title="文章列表" onclick="switchLeftNav(event, this, 'listPanel'); openPreviewTab('posts', '📋 文章列表', 'https://demo.mycompany.website/posts/')">
            <svg class="left-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
            文章列表
            <span class="nav-badge">8</span>
          </a>
          <button class="left-nav-chevron-btn" type="button" onclick="toggleLeftSubmenu(this)" title="展开/折叠子菜单">
            <svg class="left-nav-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M9 18l6-6-6-6"/>
            </svg>
          </button>
        </div>
        <div class="left-nav-submenu" style="display:none">
          <a class="left-nav-item" href="#" style="padding-left:32px" data-preview-page="post-detail" title="行业趋势 2026" onclick="switchLeftNav(event, this, ''); openPreviewTab('post-trends', '🏷 行业趋势 2026', 'https://demo.mycompany.website/posts/industry-trends-2026/')">
            <svg class="left-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            行业趋势 2026
          </a>
          <a class="left-nav-item" href="#" style="padding-left:32px" data-preview-page="post-detail" title="办公空间设计指南" onclick="switchLeftNav(event, this, ''); openPreviewTab('post-office', '🏷 办公空间设计指南', 'https://demo.mycompany.website/posts/office-design-guide/')">
            <svg class="left-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            办公空间设计指南
          </a>
        </div>
      </div>

      <div class="left-nav-section-title">站点</div>
      <a class="left-nav-item" href="#" data-panel="templates" title="模板库" onclick="switchLeftNav(event, this, 'templatesPanel')">
        <svg class="left-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
        模板库
      </a>
    </div>
  </nav>

  <!-- 左侧栏拖拽分隔条 -->
  <div class="resizer-handle" id="leftNavResizer" title="拖拽调整宽度"></div>

  <button class="sidebar-toggle-btn" id="sidebarToggleBtn" title="收起/展开侧栏">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <line x1="4" y1="6" x2="20" y2="6"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="18" x2="20" y2="18"/>
    </svg>
  </button>

  <!-- ====== 中栏：预览 ====== -->
  <section class="flex-grow-1 d-flex flex-column overflow-hidden bg-light">

    <!-- ---- 预览标签栏 ---- -->
    <div class="preview-tab-bar" id="previewTabBar">
      <!-- JS 动态填充 -->
    </div>

    <!-- ---- URL 栏 ---- -->
    <div class="preview-url-bar" id="previewUrlBar">
      <svg class="url-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
      <span class="url-text" id="previewUrlText">https://demo.mycompany.website/</span>
    </div>

    <!-- ---- 工具栏 ---- -->
    <div class="bg-white border-bottom d-flex align-items-center justify-content-center px-2 py-2 gap-1 flex-shrink-0 position-relative">
      <button class="btn btn-sm btn-outline-secondary active preview-device-btn" data-device="desktop" onclick="switchDevice('desktop')" title="电脑">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
        <span class="ms-1 d-none d-sm-inline">电脑</span>
      </button>
      <button class="btn btn-sm btn-outline-secondary preview-device-btn" data-device="tablet" onclick="switchDevice('tablet')" title="平板">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="2" ry="2"/><line x1="12" y1="18" x2="12" y2="18"/></svg>
        <span class="ms-1 d-none d-sm-inline">平板</span>
      </button>
      <button class="btn btn-sm btn-outline-secondary preview-device-btn" data-device="mobile" onclick="switchDevice('mobile')" title="手机">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="2" width="14" height="20" rx="2" ry="2"/><line x1="12" y1="18" x2="12" y2="18"/></svg>
        <span class="ms-1 d-none d-sm-inline">手机</span>
      </button>
      <button class="btn btn-sm btn-outline-secondary position-absolute" style="right:8px;" onclick="demoToast('预览已刷新')">刷新预览</button>
      <button id="reopenPanelBtn" class="btn btn-sm btn-outline-secondary position-absolute" style="right:96px;display:none;" onclick="toggleRightPanel()" title="打开属性面板">☰ 属性</button>
    </div>

    <!-- ---- iframe 预览区 ---- -->
    <div class="flex-grow-1 overflow-auto d-flex justify-content-center p-3" style="background:#e8eaed">
      <iframe class="border-0 bg-white shadow rounded preview-frame desktop" id="previewFrame"
              srcdoc="
&lt;!DOCTYPE html&gt;
&lt;html lang=&quot;zh-CN&quot;&gt;
&lt;head&gt;&lt;meta charset=&quot;UTF-8&quot;&gt;&lt;style&gt;
body{{margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Noto Sans SC',sans-serif;color:#1e293b;line-height:1.6}}
.demo-page{{padding:48px 24px;max-width:960px;margin:0 auto}}
h1{{font-size:2rem;margin-bottom:8px;color:#0f172a}}
p.subtitle{{color:#64748b;margin-bottom:32px;font-size:1.1rem}}
.cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px}}
.card{{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:20px;box-shadow:0 1px 3px rgba(0,0,0,.04)}}
.card h3{{margin:0 0 8px;font-size:1.1rem;color:#0f172a}}
.card p{{margin:0;color:#64748b;font-size:.9rem}}
&lt;/style&gt;&lt;/head&gt;
&lt;body&gt;
&lt;div class=&quot;demo-page&quot;&gt;
&lt;h1&gt;欢迎来到演示站点&lt;/h1&gt;
&lt;p class=&quot;subtitle&quot;&gt;这是一个静态演示页面，用于展示后台预览效果。实际使用时这里会显示您网站的完整 HTML。&lt;/p&gt;
&lt;div class=&quot;cards&quot;&gt;
&lt;div class=&quot;card&quot;&gt;&lt;h3&gt;🏗 产品展示&lt;/h3&gt;&lt;p&gt;12 款产品已上线，覆盖展示道具、静音舱、智能展柜等多个品类。&lt;/p&gt;&lt;/div&gt;
&lt;div class=&quot;card&quot;&gt;&lt;h3&gt;📰 行业洞察&lt;/h3&gt;&lt;p&gt;8 篇文章，涵盖行业趋势、设计指南和技术白皮书。&lt;/p&gt;&lt;/div&gt;
&lt;div class=&quot;card&quot;&gt;&lt;h3&gt;📞 联系我们&lt;/h3&gt;&lt;p&gt;专业团队 7×24 小时响应，为您的项目提供定制化解决方案。&lt;/p&gt;&lt;/div&gt;
&lt;/div&gt;
&lt;/div&gt;
&lt;/body&gt;&lt;/html&gt;">
      </iframe>
    </div>
  </section>

  <!-- 拖拽分隔条 -->
  <div class="resizer-handle" id="panelResizer" title="拖拽调整宽度"></div>

  <!-- 折叠按钮 -->
  <div class="panel-collapse-anchor">
    <button class="panel-collapse-btn" id="panelCollapseBtn" onclick="togglePanelCollapse()" title="收起面板">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
    </button>
  </div>

  <!-- ====== 右栏：属性面板 ====== -->
  <aside class="right-panel bg-white border-start flex-shrink-0 d-flex flex-column" style="width:380px" id="rightPanel">
    <div class="right-panel-header d-flex align-items-center justify-content-between flex-shrink-0">
      <div class="d-flex align-items-center gap-2">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-muted"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
        <span class="fw-semibold small" id="rightPanelTitle">首页模块</span>
      </div>
      <button class="btn btn-sm btn-outline-secondary" onclick="demoToast('预览已刷新')">刷新预览</button>
    </div>
    <div class="right-panel-body flex-grow-1 overflow-auto" id="rightPanelBody">

<!-- ====== 首页模块编辑器（假数据） ====== -->
<div class="d-flex align-items-center justify-content-between mb-3">
  <span class="fw-semibold">首页模块</span>
  <button class="btn btn-sm btn-outline-secondary" onclick="demoToast('预览已刷新')">刷新预览</button>
</div>

<div class="mb-3">
  <button class="btn btn-outline-primary btn-sm w-100" type="button" data-bs-toggle="modal" data-bs-target="#blockPaletteModal">
    + 添加模块
  </button>
</div>

<!-- 可用模块弹框 -->
<div class="modal fade" id="blockPaletteModal" tabindex="-1">
  <div class="modal-dialog modal-lg">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">可用模块</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        <div class="row g-3">
          <div class="col-6"><div class="block-palette-card card p-3" data-block-name="hero_banner" onclick="demoToast('已添加: 横幅轮播')">
            <div class="d-flex align-items-start gap-3">
              <div class="block-palette-icon flex-shrink-0"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/></svg></div>
              <div class="min-w-0"><div class="fw-semibold small mb-1">横幅轮播</div><div class="text-muted" style="font-size:11px;line-height:1.4">全屏图片/视频轮播，支持多张幻灯片</div></div>
            </div>
          </div></div>
          <div class="col-6"><div class="block-palette-card card p-3" data-block-name="section_title" onclick="demoToast('已添加: 分区标题')">
            <div class="d-flex align-items-start gap-3">
              <div class="block-palette-icon flex-shrink-0"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="4" y1="9" x2="20" y2="9"/><line x1="4" y1="15" x2="20" y2="15"/></svg></div>
              <div class="min-w-0"><div class="fw-semibold small mb-1">分区标题</div><div class="text-muted" style="font-size:11px;line-height:1.4">带标签+标题+描述的分区头部</div></div>
            </div>
          </div></div>
          <div class="col-6"><div class="block-palette-card card p-3" data-block-name="highlight_card" onclick="demoToast('已添加: 图文卡片')">
            <div class="d-flex align-items-start gap-3">
              <div class="block-palette-icon flex-shrink-0"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/></svg></div>
              <div class="min-w-0"><div class="fw-semibold small mb-1">图文卡片</div><div class="text-muted" style="font-size:11px;line-height:1.4">图文并排的宣传卡片</div></div>
            </div>
          </div></div>
          <div class="col-6"><div class="block-palette-card card p-3" data-block-name="data_grid" onclick="demoToast('已添加: 数据网格')">
            <div class="d-flex align-items-start gap-3">
              <div class="block-palette-icon flex-shrink-0"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg></div>
              <div class="min-w-0"><div class="fw-semibold small mb-1">数据网格</div><div class="text-muted" style="font-size:11px;line-height:1.4">从数据集自动展示卡片网格</div></div>
            </div>
          </div></div>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- 已选模块列表 -->
<div>
  <div class="small text-muted mb-2">已选模块（拖拽排序 | 点击配置）</div>

  <!-- 模块 0: hero_banner -->
  <div class="card mb-2 module-item expanded" data-index="0" style="cursor:move">
    <div class="d-flex align-items-center justify-content-between p-2 module-header" onclick="this.closest('.module-item').classList.toggle('expanded');var cfg=this.nextElementSibling.nextElementSibling;if(cfg)cfg.style.display=this.closest('.module-item').classList.contains('expanded')?'block':'none'">
      <span class="small fw-semibold">横幅轮播</span>
      <div class="d-flex gap-1">
        <button type="button" class="btn btn-sm btn-outline-secondary" style="font-size:10px" onclick="event.stopPropagation();demoToast('模块已移除')">✕</button>
      </div>
    </div>
    <input type="hidden" name="module_0_type" value="hero_banner">
    <input type="hidden" name="module_0_order" value="1">
    <div class="module-config p-2 border-top" style="display:block">
      <div class="device-config device-desktop">
        <div class="mb-2"><label class="form-label small mb-1 text-muted">主标题</label><input type="text" class="form-control form-control-sm" name="module_0_data_title" value="专业展示道具定制开发"></div>
        <div class="mb-2"><label class="form-label small mb-1 text-muted">副标题</label><input type="text" class="form-control form-control-sm" name="module_0_data_subtitle" value="为博物馆、商场、展览馆提供智能展示解决方案"></div>
        <div class="row g-2">
          <div class="col-6"><label class="form-label small mb-1 text-muted">主按钮文字</label><input type="text" class="form-control form-control-sm" name="module_0_data_primaryBtn" value="了解产品"></div>
          <div class="col-6"><label class="form-label small mb-1 text-muted">主按钮链接</label><input type="text" class="form-control form-control-sm" name="module_0_data_primaryLink" value="/products/"></div>
        </div>
        <div class="row g-2 mt-2">
          <div class="col-6"><label class="form-label small mb-1 text-muted">副按钮文字</label><input type="text" class="form-control form-control-sm" name="module_0_data_secondaryBtn" value="联系我们"></div>
          <div class="col-6"><label class="form-label small mb-1 text-muted">副按钮链接</label><input type="text" class="form-control form-control-sm" name="module_0_data_secondaryLink" value="/contact/"></div>
        </div>
        <div class="mb-2 mt-2"><label class="form-label small mb-1 text-muted">背景图片</label>
          <input type="text" class="form-control form-control-sm" name="module_0_data_image" value="/assets/uploads/hero-banner-demo.webp" oninput="updateImagePreview(this)">
          <label class="d-flex align-items-center gap-2 mt-1 px-3 py-2 rounded-2" style="border:1px dashed #cbd5e1;background:#f8fafc;cursor:pointer;font-size:12px;color:#64748b;transition:border-color .15s,background .15s" onmouseenter="this.style.borderColor='#94a3b8';this.style.background='#f1f5f9'" onmouseleave="this.style.borderColor='#cbd5e1';this.style.background='#f8fafc'"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12"/></svg>上传图片<input type="file" name="module_0_data_image_file" accept="image/*" style="display:none"></label>
          <div class="form-text mt-1">支持 JPG/PNG/GIF/WebP，最大 12MB</div>
          <div class="mt-2 module-image-preview"><div style="position:relative;display:inline-block"><img src="" style="max-width:120px;max-height:90px;border-radius:4px;border:1px solid #dee2e6;cursor:pointer" onclick="enlargeImage(this)" onerror="this.parentElement.parentElement.style.display='none'"><button type="button" class="btn btn-sm" onclick="this.closest('.module-image-preview').style.display='none'" style="position:absolute;top:-8px;right:-8px;width:22px;height:22px;border-radius:50%;background:#dc3545;color:#fff;font-size:12px;line-height:1;padding:0;display:flex;align-items:center;justify-content:center" title="移除">×</button></div></div>
        </div>
      </div>
    </div>
  </div>

  <!-- 模块 1: section_title -->
  <div class="card mb-2 module-item" data-index="1" style="cursor:move">
    <div class="d-flex align-items-center justify-content-between p-2 module-header" onclick="this.closest('.module-item').classList.toggle('expanded');var cfg=this.nextElementSibling.nextElementSibling;if(cfg)cfg.style.display=this.closest('.module-item').classList.contains('expanded')?'block':'none'">
      <span class="small fw-semibold">分区标题</span>
      <div class="d-flex gap-1">
        <button type="button" class="btn btn-sm btn-outline-secondary" style="font-size:10px" onclick="event.stopPropagation();demoToast('模块已移除')">✕</button>
      </div>
    </div>
    <input type="hidden" name="module_1_type" value="section_title">
    <input type="hidden" name="module_1_order" value="2">
    <div class="module-config p-2 border-top" style="display:none">
      <div class="device-config device-desktop">
        <div class="mb-2"><label class="form-label small mb-1 text-muted">标签文字</label><input type="text" class="form-control form-control-sm" name="module_1_data_tag" value="产品展示" placeholder="模块上方小标签"></div>
        <div class="mb-2"><label class="form-label small mb-1 text-muted">标题</label><input type="text" class="form-control form-control-sm" name="module_1_data_title" value="热门产品推荐"></div>
        <div class="mb-2"><label class="form-label small mb-1 text-muted">描述文字</label><textarea class="form-control form-control-sm" rows="2" name="module_1_data_desc">精选优质展示道具，为客户提供最佳展示体验</textarea></div>
        <hr class="my-2">
        <div class="small fw-semibold mb-1 text-muted">颜色</div>
        <div class="row g-2">
          <div class="col-6"><label class="form-label small mb-1 text-muted">外层背景色</label><div class="input-group input-group-sm"><input type="color" class="form-control form-control-color" value="#f8fafc"><input type="text" class="form-control form-control-sm" name="module_1_data_section_bg" value="#f8fafc" placeholder="选择颜色"></div></div>
          <div class="col-6"><label class="form-label small mb-1 text-muted">标题颜色</label><div class="input-group input-group-sm"><input type="color" class="form-control form-control-color" value="#0f172a"><input type="text" class="form-control form-control-sm" name="module_1_data_title_color" value="#0f172a" placeholder="选择颜色"></div></div>
        </div>
      </div>
    </div>
  </div>

  <!-- 模块 2: highlight_card -->
  <div class="card mb-2 module-item" data-index="2" style="cursor:move">
    <div class="d-flex align-items-center justify-content-between p-2 module-header" onclick="this.closest('.module-item').classList.toggle('expanded');var cfg=this.nextElementSibling.nextElementSibling;if(cfg)cfg.style.display=this.closest('.module-item').classList.contains('expanded')?'block':'none'">
      <span class="small fw-semibold">图文卡片</span>
      <div class="d-flex gap-1">
        <button type="button" class="btn btn-sm btn-outline-secondary" style="font-size:10px" onclick="event.stopPropagation();demoToast('模块已移除')">✕</button>
      </div>
    </div>
    <input type="hidden" name="module_2_type" value="highlight_card">
    <input type="hidden" name="module_2_order" value="3">
    <div class="module-config p-2 border-top" style="display:none">
      <div class="device-config device-desktop">
        <div class="mb-2"><label class="form-label small mb-1 text-muted">标题</label><input type="text" class="form-control form-control-sm" name="module_2_data_title" value="智能静音舱系列"></div>
        <div class="mb-2"><label class="form-label small mb-1 text-muted">描述</label><textarea class="form-control form-control-sm" rows="3" name="module_2_data_desc">采用航空级隔音材料，配备智能温控与通风系统，为企业打造专注高效的私密办公空间。</textarea></div>
        <div class="row g-2">
          <div class="col-6"><label class="form-label small mb-1 text-muted">按钮文字</label><input type="text" class="form-control form-control-sm" name="module_2_data_btn_text" value="了解更多"></div>
          <div class="col-6"><label class="form-label small mb-1 text-muted">按钮链接</label><input type="text" class="form-control form-control-sm" name="module_2_data_btn_url" value="/products/silent-booth/"></div>
        </div>
        <div class="mb-2 mt-2"><label class="form-label small mb-1 text-muted">图片</label>
          <input type="text" class="form-control form-control-sm" name="module_2_data_image" value="/assets/uploads/highlight-demo.webp" oninput="updateImagePreview(this)">
          <label class="d-flex align-items-center gap-2 mt-1 px-3 py-2 rounded-2" style="border:1px dashed #cbd5e1;background:#f8fafc;cursor:pointer;font-size:12px;color:#64748b;transition:border-color .15s,background .15s" onmouseenter="this.style.borderColor='#94a3b8';this.style.background='#f1f5f9'" onmouseleave="this.style.borderColor='#cbd5e1';this.style.background='#f8fafc'"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12"/></svg>上传图片<input type="file" name="module_2_data_image_file" accept="image/*" style="display:none"></label>
          <div class="form-text mt-1">支持 JPG/PNG/GIF/WebP，最大 12MB</div>
          <div class="mt-2 module-image-preview"><div style="position:relative;display:inline-block"><img src="" style="max-width:120px;max-height:90px;border-radius:4px;border:1px solid #dee2e6;cursor:pointer" onclick="enlargeImage(this)" onerror="this.parentElement.parentElement.style.display='none'"><button type="button" class="btn btn-sm" onclick="this.closest('.module-image-preview').style.display='none'" style="position:absolute;top:-8px;right:-8px;width:22px;height:22px;border-radius:50%;background:#dc3545;color:#fff;font-size:12px;line-height:1;padding:0;display:flex;align-items:center;justify-content:center" title="移除">×</button></div></div>
        </div>
      </div>
    </div>
  </div>

</div>

<div class="mt-2 d-flex gap-2">
  <button type="button" class="btn btn-primary btn-sm" onclick="demoToast('已保存（演示模式）')">保存模块配置</button>
</div>

    </div>
    <div class="right-panel-footer flex-shrink-0" id="rightPanelFooter" style="display:none;"></div>
  </aside>
</div>

<!-- 拖拽遮罩 -->
<div id="dragOverlay" style="display:none;position:fixed;inset:0;z-index:9999;background:transparent;cursor:col-resize;"></div>

<!-- ====== 页面选择器模态框 ====== -->
<div class="modal fade page-tree-modal" id="pageTreeModal" tabindex="-1">
  <div class="modal-dialog modal-sm">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">选择页面</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        <input type="text" class="form-control form-control-sm page-tree-search" id="pageTreeSearch" placeholder="搜索页面…" oninput="filterPageTree()">
        <div id="pageTreeList">
          <div class="page-tree-item" data-title="首页" data-url="https://demo.mycompany.website/" data-key="home" onclick="openPreviewTab('home', '🏠 首页', this.dataset.url);bootstrap.Modal.getInstance(document.getElementById('pageTreeModal')).hide()">
            <svg class="page-tree-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg>🏠 首页
          </div>
          <div class="page-tree-item" data-title="关于我们" data-url="https://demo.mycompany.website/about/" data-key="about" onclick="openPreviewTab('about', '📄 关于我们', this.dataset.url);bootstrap.Modal.getInstance(document.getElementById('pageTreeModal')).hide()">
            <svg class="page-tree-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/></svg>📄 关于我们
          </div>
          <div class="page-tree-category">📋 产品列表</div>
          <div class="page-tree-item page-tree-child" data-title="静音舱-3000" data-url="https://demo.mycompany.website/products/silent-booth-3000/" data-key="product-sb3000" onclick="openPreviewTab('product-sb3000', '🏷 静音舱-3000', this.dataset.url);bootstrap.Modal.getInstance(document.getElementById('pageTreeModal')).hide()">
            <svg class="page-tree-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/></svg>静音舱-3000
          </div>
          <div class="page-tree-item page-tree-child" data-title="静音舱-5000" data-url="https://demo.mycompany.website/products/silent-booth-5000/" data-key="product-sb5000" onclick="openPreviewTab('product-sb5000', '🏷 静音舱-5000', this.dataset.url);bootstrap.Modal.getInstance(document.getElementById('pageTreeModal')).hide()">
            <svg class="page-tree-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/></svg>静音舱-5000
          </div>
          <div class="page-tree-item page-tree-child" data-title="展示柜-8000" data-url="https://demo.mycompany.website/products/showcase-8000/" data-key="product-sc8000" onclick="openPreviewTab('product-sc8000', '🏷 展示柜-8000', this.dataset.url);bootstrap.Modal.getInstance(document.getElementById('pageTreeModal')).hide()">
            <svg class="page-tree-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/></svg>展示柜-8000
          </div>
          <div class="page-tree-category">📋 文章列表</div>
          <div class="page-tree-item page-tree-child" data-title="行业趋势 2026" data-url="https://demo.mycompany.website/posts/industry-trends-2026/" data-key="post-trends" onclick="openPreviewTab('post-trends', '🏷 行业趋势 2026', this.dataset.url);bootstrap.Modal.getInstance(document.getElementById('pageTreeModal')).hide()">
            <svg class="page-tree-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/></svg>行业趋势 2026
          </div>
          <div class="page-tree-item page-tree-child" data-title="办公空间设计指南" data-url="https://demo.mycompany.website/posts/office-design-guide/" data-key="post-office" onclick="openPreviewTab('post-office', '🏷 办公空间设计指南', this.dataset.url);bootstrap.Modal.getInstance(document.getElementById('pageTreeModal')).hide()">
            <svg class="page-tree-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/></svg>办公空间设计指南
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- ====== 脚本 ====== -->
<script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.8/dist/umd/popper.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.min.js"></script>
<script>
// ---- 演示 toast ----
function demoToast(msg) {{
  var t = document.createElement('div');
  t.className = 'toast-notice'; t.textContent = msg;
  t.style.cssText = 'position:fixed;bottom:24px;left:50%;transform:translateX(-50%);z-index:99999;background:#0f172a;color:#fff;padding:8px 20px;border-radius:8px;font-size:13px;box-shadow:0 4px 16px rgba(0,0,0,.25);pointer-events:none;transition:opacity .3s';
  document.body.appendChild(t);
  setTimeout(function(){{ t.style.opacity = '0'; setTimeout(function(){{ t.remove(); }}, 300); }}, 1500);
}}

// ---- 左侧导航切换 ----
function switchLeftNav(e, link, panelName) {{
  if (e) e.preventDefault();
  document.querySelectorAll('.left-nav-item').forEach(function(el) {{ el.classList.remove('active'); }});
  if (link) link.classList.add('active');
  var title = document.getElementById('rightPanelTitle');
  if (title && panelName) title.textContent = panelName === 'homePanel' ? '首页模块' : (link ? link.title || link.textContent.trim() : '属性');
}}

// ---- 左侧子菜单展开/折叠 ----
function toggleLeftSubmenu(button) {{
  var group = button.closest('.left-nav-group');
  if (!group) return;
  var submenu = group.querySelector('.left-nav-submenu');
  var chevron = button.querySelector('.left-nav-chevron');
  if (!submenu) return;
  var isOpen = submenu.style.display === 'block';
  submenu.style.display = isOpen ? 'none' : 'block';
  if (chevron) chevron.classList.toggle('open', !isOpen);
}}

// ---- 预览标签栏 ----
var previewTabs = [];
var activeTabKey = null;

function renderTabBar() {{
  var bar = document.getElementById('previewTabBar');
  var html = '';
  previewTabs.forEach(function(tab) {{
    var cls = tab.key === activeTabKey ? ' active' : '';
    html += '<div class="preview-tab' + cls + '" data-tab-key="' + tab.key + '" onclick="switchPreviewTab(\'' + tab.key + '\')">';
    html += '<span class="tab-favicon" style="background:' + (tab.key === 'home' ? '#067a7a' : tab.key.indexOf('product') === 0 ? '#f97316' : '#94a3b8') + '"></span>';
    html += '<span class="tab-title">' + tab.title + '</span>';
    if (previewTabs.length > 1) {{
      html += '<button class="tab-close" onclick="event.stopPropagation();closePreviewTab(\'' + tab.key + '\')">×</button>';
    }}
    html += '</div>';
  }});
  html += '<button class="preview-tab-add" title="新建标签" data-bs-toggle="modal" data-bs-target="#pageTreeModal">+</button>';
  bar.innerHTML = html;
}}

function updateUrlBar(url) {{
  document.getElementById('previewUrlText').textContent = url || 'about:blank';
}}

function openPreviewTab(key, title, url) {{
  var existing = previewTabs.find(function(t) {{ return t.key === key; }});
  if (existing) {{
    switchPreviewTab(key);
    return;
  }}
  previewTabs.push({{ key: key, title: title, url: url }});
  activeTabKey = key;
  renderTabBar();
  updateUrlBar(url);
}}

function switchPreviewTab(key) {{
  activeTabKey = key;
  var tab = previewTabs.find(function(t) {{ return t.key === key; }});
  renderTabBar();
  if (tab) updateUrlBar(tab.url);
}}

function closePreviewTab(key) {{
  if (previewTabs.length <= 1) return;
  var idx = previewTabs.findIndex(function(t) {{ return t.key === key; }});
  if (idx === -1) return;
  previewTabs.splice(idx, 1);
  if (activeTabKey === key) {{
    var newIdx = Math.min(idx, previewTabs.length - 1);
    activeTabKey = previewTabs[newIdx].key;
    updateUrlBar(previewTabs[newIdx].url);
  }}
  renderTabBar();
}}

// ---- 页面选择器搜索过滤 ----
function filterPageTree() {{
  var q = (document.getElementById('pageTreeSearch').value || '').toLowerCase();
  document.querySelectorAll('#pageTreeList .page-tree-item').forEach(function(item) {{
    var title = (item.dataset.title || '').toLowerCase();
    item.style.display = (!q || title.indexOf(q) !== -1) ? '' : 'none';
  }});
  document.querySelectorAll('#pageTreeList .page-tree-category').forEach(function(cat) {{
    cat.style.display = q ? 'none' : '';
  }});
}}

// ---- 设备切换 ----
function switchDevice(device) {{
  document.querySelectorAll('.preview-device-btn').forEach(function(b) {{ b.classList.remove('active'); }});
  var btn = document.querySelector('[data-device="' + device + '"]');
  if (btn) btn.classList.add('active');
  var frame = document.getElementById('previewFrame');
  frame.classList.remove('desktop','tablet','mobile');
  frame.classList.add(device);
}}

// ---- 右侧面板显示/隐藏 ----
function toggleRightPanel() {{
  var panel = document.getElementById('rightPanel');
  var reopenBtn = document.getElementById('reopenPanelBtn');
  var collapseBtn = document.getElementById('panelCollapseBtn');
  if (panel.classList.contains('d-none')) {{
    panel.classList.remove('d-none');
    if (panel.classList.contains('panel-collapsed')) {{
      panel.classList.remove('panel-collapsed');
      panel.style.width = (panel.dataset.savedWidth || '380') + 'px';
    }}
    if (reopenBtn) reopenBtn.style.display = 'none';
    if (collapseBtn) {{
      collapseBtn.style.display = '';
      collapseBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>';
      collapseBtn.title = '收起面板';
    }}
  }} else {{
    panel.classList.add('d-none');
    if (reopenBtn) reopenBtn.style.display = '';
    if (collapseBtn) collapseBtn.style.display = 'none';
  }}
}}

function togglePanelCollapse() {{
  var panel = document.getElementById('rightPanel');
  var btn = document.getElementById('panelCollapseBtn');
  if (!panel) return;
  if (panel.classList.contains('panel-collapsed')) {{
    var savedWidth = panel.dataset.savedWidth || '380';
    panel.style.width = savedWidth + 'px';
    panel.classList.remove('panel-collapsed');
    if (btn) {{
      btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>';
      btn.title = '收起面板';
    }}
  }} else {{
    panel.dataset.savedWidth = panel.offsetWidth;
    panel.classList.add('panel-collapsed');
    if (btn) {{
      btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>';
      btn.title = '展开面板';
    }}
  }}
}}

// ---- 图片预览 ----
function enlargeImage(img) {{
  var src = img.src;
  if (!src) return;
  var overlay = document.getElementById('imgLightbox');
  if (!overlay) {{
    overlay = document.createElement('div');
    overlay.id = 'imgLightbox';
    overlay.style.cssText = 'position:fixed;inset:0;z-index:99999;background:rgba(0,0,0,.85);display:flex;align-items:center;justify-content:center;cursor:pointer';
    overlay.onclick = function() {{ overlay.style.display = 'none'; }};
    var lbImg = document.createElement('img');
    lbImg.style.cssText = 'max-width:95vw;max-height:95vh;border-radius:6px;box-shadow:0 4px 30px rgba(0,0,0,.5)';
    overlay.appendChild(lbImg);
    document.body.appendChild(overlay);
  }}
  overlay.querySelector('img').src = src;
  overlay.style.display = 'flex';
}}

function updateImagePreview(urlInput) {{
  var container = urlInput.closest('.mb-2');
  var preview = container ? container.querySelector('.module-image-preview') : null;
  var img = preview ? preview.querySelector('img') : null;
  if (!preview || !img) return;
  var url = urlInput.value.trim();
  if (url) {{ img.src = url; preview.style.display = ''; }}
  else {{ preview.style.display = 'none'; img.src = ''; }}
}}

// ---- 面板拖拽 ----
(function(){{
  var handle = document.getElementById('panelResizer');
  var panel = document.getElementById('rightPanel');
  var overlay = document.getElementById('dragOverlay');
  if (!handle || !panel) return;
  var dragging = false, startX = 0, startWidth = 0;
  function begin(e) {{
    e.preventDefault(); dragging = true; startX = e.clientX; startWidth = panel.offsetWidth;
    handle.classList.add('dragging'); document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none'; overlay.style.display = 'block';
  }}
  function move(e) {{
    if (!dragging) return;
    panel.style.width = Math.max(240, Math.min(900, startWidth + (startX - e.clientX))) + 'px';
  }}
  function end() {{
    if (!dragging) return;
    dragging = false; handle.classList.remove('dragging');
    document.body.style.cursor = ''; document.body.style.userSelect = '';
    overlay.style.display = 'none';
  }}
  handle.addEventListener('mousedown', begin);
  overlay.addEventListener('mousemove', move);
  overlay.addEventListener('mouseup', end);
  overlay.addEventListener('mouseleave', end);
}})();

// ---- 左侧栏拖拽 ----
(function(){{
  var handle = document.getElementById('leftNavResizer');
  var leftNav = document.getElementById('leftNav');
  var toggleBtn = document.getElementById('sidebarToggleBtn');
  var overlay = document.getElementById('dragOverlay');
  if (!handle || !leftNav) return;
  var THRESHOLD = 140;
  var dragging = false, startX = 0, startWidth = 0;
  function setBtnAppearance(collapsed) {{
    if (!toggleBtn) return;
    if (collapsed) {{
      toggleBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="13 17 18 12 13 7"/><polyline points="6 17 11 12 6 7"/></svg>';
      toggleBtn.title = '展开侧栏';
    }} else {{
      toggleBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="6" x2="20" y2="6"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="18" x2="20" y2="18"/></svg>';
      toggleBtn.title = '收起侧栏';
    }}
  }}
  function begin(e) {{
    e.preventDefault(); dragging = true; startX = e.clientX; startWidth = leftNav.offsetWidth;
    handle.classList.add('dragging'); document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none'; overlay.style.display = 'block';
  }}
  function move(e) {{
    if (!dragging) return;
    var w = Math.max(60, Math.min(480, startWidth + (e.clientX - startX)));
    leftNav.style.setProperty('width', w + 'px', 'important');
    leftNav.style.setProperty('min-width', w + 'px', 'important');
    leftNav.style.transition = 'none';
    if (toggleBtn) {{ toggleBtn.style.left = (w - 12) + 'px'; toggleBtn.style.transition = 'none'; }}
    if (w < THRESHOLD && !leftNav.classList.contains('left-nav-collapsed')) {{
      leftNav.classList.add('left-nav-collapsed'); setBtnAppearance(true);
    }} else if (w >= THRESHOLD && leftNav.classList.contains('left-nav-collapsed')) {{
      leftNav.classList.remove('left-nav-collapsed'); setBtnAppearance(false);
    }}
  }}
  function end() {{
    if (!dragging) return;
    dragging = false; handle.classList.remove('dragging');
    document.body.style.cursor = ''; document.body.style.userSelect = '';
    overlay.style.display = 'none'; leftNav.style.transition = '';
    if (toggleBtn) toggleBtn.style.transition = '';
    var finalWidth = leftNav.offsetWidth;
    if (finalWidth < THRESHOLD) {{
      leftNav.style.removeProperty('width'); leftNav.style.removeProperty('min-width');
      if (toggleBtn) toggleBtn.style.removeProperty('left');
      leftNav.classList.add('left-nav-collapsed'); setBtnAppearance(true);
    }} else {{
      leftNav.classList.remove('left-nav-collapsed'); setBtnAppearance(false);
    }}
  }}
  handle.addEventListener('mousedown', begin);
  overlay.addEventListener('mousemove', move);
  overlay.addEventListener('mouseup', end);
  overlay.addEventListener('mouseleave', end);
}})();

// ---- 颜色选择器 ----
function initColorPickers() {{
  document.querySelectorAll('input.form-control-color[type="color"]').forEach(function(colorInput) {{
    if (colorInput.closest('.color-swatch')) return;
    var group = colorInput.closest('.input-group');
    if (!group) return;
    var textInput = group.querySelector('input[type=text]');
    var hasValue = textInput && textInput.value.trim() !== '';
    var swatch = document.createElement('label');
    swatch.className = 'color-swatch' + (hasValue ? '' : ' color-empty');
    swatch.style.background = hasValue ? textInput.value : '#ffffff';
    colorInput.classList.remove('form-control-color');
    colorInput.style.cssText = 'position:absolute;top:-8px;left:-8px;width:calc(100%+16px);height:calc(100%+16px);opacity:0;cursor:pointer;border:none;padding:0;';
    colorInput.setAttribute('oninput', "var p=this.parentElement;p.style.background=this.value;p.classList.remove('color-empty');var t=p.parentElement.querySelector('input[type=text]');if(t)t.value=this.value");
    if (textInput) {{
      textInput.placeholder = '选择颜色';
      textInput.setAttribute('oninput', "var g=this.parentElement;var c=g.querySelector('input[type=color]');var l=g.querySelector('.color-swatch');if(c)c.value=this.value;if(l){{l.style.background=this.value;l.classList.remove('color-empty')}}");
    }}
    swatch.appendChild(colorInput);
    group.insertBefore(swatch, group.firstChild);
  }});
}}

// ---- 侧栏 hover tooltip ----
(function(){{
  var nav = document.getElementById('leftNav');
  var tooltip = document.createElement('div');
  tooltip.id = 'leftNavTooltip';
  tooltip.style.cssText = 'position:fixed;pointer-events:none;z-index:10000;padding:6px 12px;background:#0f172a;color:#f1f5f9;font-size:12px;font-weight:500;line-height:1.4;border-radius:6px;white-space:nowrap;box-shadow:0 4px 14px rgba(0,0,0,.35);opacity:0;visibility:hidden;transition:opacity 0.12s,visibility 0.12s;';
  document.body.appendChild(tooltip);
  var timer = null, collapsed = false;

  function showTooltip(item) {{
    if (!collapsed) return;
    var title = item.getAttribute('title');
    if (!title) return;
    var rect = item.getBoundingClientRect();
    tooltip.textContent = title;
    tooltip.style.left = (rect.right + 10) + 'px';
    tooltip.style.top = (rect.top + rect.height / 2) + 'px';
    tooltip.style.transform = 'translateY(-50%)';
    tooltip.style.opacity = '1'; tooltip.style.visibility = 'visible';
  }}

  nav.addEventListener('mouseover', function(e) {{
    if (!collapsed) return;
    var item = e.target.closest('.left-nav-item');
    if (!item) {{ tooltip.style.opacity = '0'; tooltip.style.visibility = 'hidden'; return; }}
    clearTimeout(timer);
    timer = setTimeout(function(){{ showTooltip(item); }}, 200);
  }});
  nav.addEventListener('mouseout', function(e) {{
    clearTimeout(timer);
    tooltip.style.opacity = '0'; tooltip.style.visibility = 'hidden';
  }});

  // 侧栏收缩按钮
  var btn = document.getElementById('sidebarToggleBtn');
  if (btn) {{
    btn.addEventListener('click', function() {{
      collapsed = !collapsed;
      if (collapsed) {{
        nav.style.removeProperty('width'); nav.style.removeProperty('min-width');
        btn.style.removeProperty('left');
        nav.classList.add('left-nav-collapsed');
        btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="13 17 18 12 13 7"/><polyline points="6 17 11 12 6 7"/></svg>';
        btn.title = '展开侧栏';
        tooltip.style.opacity = '0'; tooltip.style.visibility = 'hidden';
      }} else {{
        nav.classList.remove('left-nav-collapsed');
        btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="6" x2="20" y2="6"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="18" x2="20" y2="18"/></svg>';
        btn.title = '收起侧栏';
      }}
    }});
  }}
}})();

// ---- 模块手风琴点击 ----
document.querySelectorAll('.module-item .module-header').forEach(function(header) {{
  header.addEventListener('click', function() {{
    var item = this.closest('.module-item');
    item.classList.toggle('expanded');
    var cfg = item.querySelector('.module-config');
    if (cfg) cfg.style.display = item.classList.contains('expanded') ? 'block' : 'none';
  }});
}});

// ---- 初始化 ----
document.addEventListener('DOMContentLoaded', function() {{
  initColorPickers();
  // 默认打开首页标签
  openPreviewTab('home', '🏠 首页', 'https://demo.mycompany.website/');
}});
</script>

</body>
</html>'''

OUT = HERE / "admin-dashboard-demo.html"
OUT.write_text(HTML, encoding="utf-8")
print(f"Generated: {OUT}  ({len(HTML):,} bytes)")
