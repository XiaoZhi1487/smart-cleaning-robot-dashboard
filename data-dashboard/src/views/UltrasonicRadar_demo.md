# 超声波雷达绘制代码 - 教学分段演示

> 基于当前项目 `UltrasonicRadar.vue` 的 `renderRadar()` 编写（按需绘制，无动画循环）。
> 每段代码对应 `renderRadar()` 中的一部分，可分段讲解。

---

## 第 1 段：画布与雷达网格

**讲解要点**：清空画布，绘制 4 圈同心圆并标注距离刻度（125 / 250 / 375 / 500mm）

```javascript
const ctx = canvasCtx
const centerX = radarSize / 2
const centerY = radarSize / 2
const maxRadius = Math.min(centerX, centerY) - 34

// 1. 清空画布 - 深色背景
ctx.fillStyle = '#0a101f'
ctx.fillRect(0, 0, radarSize, radarSize)

// 2. 绘制 4 圈同心圆 + 距离刻度（沿左上对角线排布，避免刻度重叠）
ctx.strokeStyle = 'rgba(0, 229, 255, 0.2)'
ctx.lineWidth = 1
const rings = [125, 250, 375, 500]
for (let i = 1; i <= 4; i++) {
  const radius = maxRadius * i / 4
  ctx.beginPath()
  ctx.arc(centerX, centerY, radius, 0, Math.PI * 2)
  ctx.stroke()
  ctx.fillStyle = 'rgba(0, 229, 255, 0.6)'
  ctx.font = '12px Consolas'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  const labelAngle = -Math.PI * 3 / 4
  ctx.fillText(rings[i-1] + 'mm', centerX + Math.cos(labelAngle) * radius,
               centerY + Math.sin(labelAngle) * radius)
}
```

---

## 第 2 段：十字线与方向标记

**讲解要点**：绘制十字基准线，以及左 / 前 / 右三个方向标签（国际化文本）

```javascript
// 3. 十字线
ctx.beginPath()
ctx.moveTo(centerX, centerY - maxRadius)
ctx.lineTo(centerX, centerY + maxRadius)
ctx.moveTo(centerX - maxRadius, centerY)
ctx.lineTo(centerX + maxRadius, centerY)
ctx.stroke()

// 4. 方向标记 - 左、前、右（t() 为 i18n 文本，随语言切换）
const directions = [t('radar.left'), t('radar.front'), t('radar.right')]
const positions = [
  { x: centerX - maxRadius - 18, y: centerY },   // 左 - 9点钟
  { x: centerX, y: centerY - maxRadius - 18 },   // 前 - 12点钟
  { x: centerX + maxRadius + 18, y: centerY }    // 右 - 3点钟
]
ctx.fillStyle = '#00E5FF'
ctx.font = '14px Microsoft YaHei'
ctx.textAlign = 'center'
ctx.textBaseline = 'middle'
positions.forEach((pos, i) => ctx.fillText(directions[i], pos.x, pos.y))
```

---

## 第 3 段：传感器数据扇形

**讲解要点**：按距离映射半径绘制扇形，过近（<200mm）变红警告，并标注距离数值

```javascript
// 5. 绘制传感器扇形 - 左、前、右（角度：PI、-PI/2、0）
const maxDistance = 500
const angles = [Math.PI, -Math.PI / 2, 0]

sensors.value.forEach((sensor, i) => {
  if (sensor.distance > 0) {
    const displayDistance = Math.min(sensor.distance, maxDistance)
    const radius = (displayDistance / maxDistance) * maxRadius
    const angle = angles[i]

    ctx.beginPath()
    ctx.moveTo(centerX, centerY)
    ctx.arc(centerX, centerY, radius, angle - Math.PI / 6, angle + Math.PI / 6)
    ctx.closePath()

    // 距离小于 200mm 变红色警告，否则青色
    if (sensor.distance < WARNING_THRESHOLD) {
      ctx.fillStyle = 'rgba(255, 51, 102, 0.6)'
      ctx.strokeStyle = '#FF3366'
    } else {
      ctx.fillStyle = 'rgba(0, 229, 255, 0.4)'
      ctx.strokeStyle = '#00E5FF'
    }
    ctx.fill()
    ctx.lineWidth = 2
    ctx.stroke()

    // 距离数值
    const textRadius = radius + 16
    ctx.fillStyle = sensor.distance < WARNING_THRESHOLD ? '#FF3366' : '#00E5FF'
    ctx.font = 'bold 14px Consolas'
    ctx.fillText(sensor.distance + 'mm',
                 centerX + Math.cos(angle) * textRadius,
                 centerY + Math.sin(angle) * textRadius)
  }
})
```

---

## 第 4 段：中心点

**讲解要点**：绘制中心点代表机器人位置

```javascript
// 6. 绘制中心点（代表机器人）
ctx.beginPath()
ctx.arc(centerX, centerY, 7, 0, Math.PI * 2)
ctx.fillStyle = '#00E5FF'
ctx.fill()
```

---

## 演示提示

- 当前 `renderRadar()` 为**按需绘制**：在 `resizeCanvas()`（窗口尺寸 / 高 DPI 变化）及数据更新时触发，不使用 `requestAnimationFrame` 循环
- 方向标签随界面语言切换实时重绘（`watch(locale, () => renderRadar())`）
- 警告阈值：`WARNING_THRESHOLD = 200`（mm），最大显示距离 500mm
- 数据来源：订阅 ROS 话题 `/wave_length`（`std_msgs/UInt8MultiArray`），每 2 字节解析一路传感器距离

---

*文档版本: v2.0 · 更新日期: 2026-10-17*
