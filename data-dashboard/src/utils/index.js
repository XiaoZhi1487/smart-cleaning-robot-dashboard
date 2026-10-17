// 数字格式化：保留1位小数
export function formatNum(num) {
    return Number(num).toFixed(1);
}

// 状态标签渲染
export function getStateTag(state) {
    switch (state) {
        case "运行中": return `<span class="normal">运行中</span>`;
        case "已停止": return `<span class="none">已停止</span>`;
        case "故障中": return `<span class="error">故障中</span>`;
        case "正常": return `<span class="normal">正常</span>`;
        case "待维保": return `<span class="warning">待维保</span>`;
        case "待维修": return `<span class="error">待维修</span>`;
        case "启用": return `<span class="normal">启用</span>`;
        case "禁用": return `<span class="none">禁用</span>`;
        default: return `<span class="none">未知</span>`;
    }
}

// 状态标签class
export function getStateClass(state) {
    switch (state) {
        case "运行中":
        case "正常":
        case "启用":
            return "normal";
        case "已停止":
        case "禁用":
            return "none";
        case "故障中":
        case "待维修":
            return "error";
        case "待维保":
            return "warning";
        default:
            return "none";
    }
}
