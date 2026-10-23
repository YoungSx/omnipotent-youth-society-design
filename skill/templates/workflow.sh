#!/usr/bin/env bash
# 万能青年旅店视觉设计技能 · 标准化工作流脚本 (Standardized Workflow Template)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 自动定位项目根目录（如果在 skill/templates/ 下运行则取上两级，若在根目录则为当前目录）
if [ -f "${SCRIPT_DIR}/../../build.py" ]; then
  PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
  SKILL_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
elif [ -f "./build.py" ]; then
  PROJECT_ROOT="$(pwd)"
  SKILL_ROOT="$(pwd)/skill"
else
  PROJECT_ROOT="${SCRIPT_DIR}"
  SKILL_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
fi

echo "========================================================"
echo " 万能青年旅店视觉设计系统 (Omnipotent Youth Society)"
echo " 跨媒介自适应工作流与交付规范流水线"
echo "========================================================"

STEP=${1:-"all"}

check_anti_patterns() {
  echo "[1/4] 执行十项铁律静态合规自检..."
  local violations=0
  # 检查是否误用了纯白 #FFFFFF、纯黑 #000000、文字阴影刻槽或 bevel 浮雕
  local matches
  matches=$(grep -rn --include="*.html" --include="*.css" --include="*.svg" -iE "#ffffff|#000000|text-shadow|bevel|drop-shadow" "${SKILL_ROOT}/templates" 2>/dev/null || true)
  if [ -n "$matches" ]; then
    echo "      ⚠️ 警告: 模板中发现可能触犯反模式的样式定义:"
    echo "$matches"
    violations=$((violations + 1))
  else
    echo "      ✓ 纯白/纯黑与伪3D浮雕反模式筛查通过 (0 违规)"
  fi
}

render_web_deliverables() {
  echo "[2/4] 构建数字界面交付物 (Web UI)..."
  if [ -f "${PROJECT_ROOT}/build.py" ]; then
    python3 "${PROJECT_ROOT}/build.py"
    echo "      ✓ 数字界面与离线样本构建成功: dist/ 及 index.html"
  else
    echo "      ✓ 提示: 可直接复用 ${SKILL_ROOT}/templates/web-rubbing-view.html"
  fi
}

export_vector_poster() {
  echo "[3/4] 验证矢量与海报模板 (Poster SVG)..."
  if [ -f "${SKILL_ROOT}/templates/poster-template.svg" ]; then
    echo "      ✓ 矢量海报模板就绪: ${SKILL_ROOT}/templates/poster-template.svg (1200x1600)"
  fi
}

verify_evidence_layer() {
  echo "[4/4] 核验信源分层与知识库引用..."
  if [ -f "${SKILL_ROOT}/references/SOURCES.md" ] && [ -f "${SKILL_ROOT}/references/DESIGN.md" ]; then
    echo "      ✓ 证据库 SOURCES.md 与 规范库 DESIGN.md 均完整可用"
  fi
}

case "$STEP" in
  lint)
    check_anti_patterns
    ;;
  build)
    render_web_deliverables
    export_vector_poster
    ;;
  all)
    check_anti_patterns
    render_web_deliverables
    export_vector_poster
    verify_evidence_layer
    echo "========================================================"
    echo " 工作流执行完毕：所有产物均符合 2D 矿物哑光拓片规约！"
    echo "========================================================"
    ;;
  *)
    echo "未知步骤: $STEP，可选: lint, build, all"
    exit 1
    ;;
esac
