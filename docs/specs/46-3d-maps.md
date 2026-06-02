# SPEC 46 — 3D Maps (Power Map)

## Mục tiêu
Geographic + temporal visualization 3D trên globe/map. Insert → 3D Map.

## Trạng thái hiện tại
- ✗ Chưa có.

## 46.1 Khái niệm

- Modern Excel: Insert → 3D Map → cửa sổ riêng (3D viewport).
- Data: cần columns có địa lý (City, State, Country, Latitude/Longitude, Zip).
- Render: globe 3D (Bing Maps) hoặc flat map → plot data points làm column/heat/region/bubble.
- Temporal: nếu có date column → animate timeline.
- Export: video / image / 3D fly-through.

## 46.2 3D Map Window Layout

```
┌─ 3D Map ────────────────────────────────────────────────────┐
│ Home  Tour  Tools                                            │
│ ──────────────────────────────────────────────────────────│
│ Scene 1 [+]  │ Layer 1                                      │
│              │ ┌─────────────────────────────────────────┐ │
│              │ │                                         │ │
│              │ │     [3D Globe viewport]                 │ │
│              │ │                                         │ │
│              │ └─────────────────────────────────────────┘ │
│              │ Layer Pane (right):                          │
│              │ - Location: City, Country                    │
│              │ - Height: Sales                              │
│              │ - Category: Product                          │
│              │ - Time: OrderDate                            │
│              │ Visualization: [Stacked Column ▼]            │
│              │ Layer Options: opacity, color...             │
│ ──────────────────────────────────────────────────────────│
│ Time slider: ──●─────────── 2026-01 → 2026-12               │
└──────────────────────────────────────────────────────────────┘
```

## 46.3 Visualizations

- **Stacked Column**: 3D column ở vị trí, height = value, stack by category.
- **Clustered Column**: tương tự nhưng side-by-side.
- **Bubble**: cầu tại vị trí, size = value.
- **Heat Map**: vùng tô màu theo density.
- **Region**: tô region (state/country) theo value.

## 46.4 Tour / Scene

- **Scenes**: snapshot view + data filter + visualization. 1 tour = nhiều scenes.
- **Transitions** giữa scenes: pan, zoom, rotation, fade.
- **Tour Playback**: play through scenes như slideshow + animation timeline.
- **Export Video**: MP4 với resolution + quality settings.

## 46.5 Custom Maps

- Insert custom map image (vd floor plan, sân vận động) thay vì world map.
- Define XY coordinate system trên image.
- Plot data points theo XY.

## Implementation note

**Out of scope** cho Ezcel. Reasons:
- 3D rendering engine (OpenGL/Vulkan/DirectX) — phức tạp.
- Bing Maps tiles licensing.
- Geocoding service (city → lat/lon) cần API.
- Time animation engine.

### Possible minimal alternative
- 2D matplotlib map plot (mpl_toolkits.basemap deprecated → cartopy hoặc folium).
- Insert → Map Chart → static image, không 3D / không animation.
- Có thể stub Map Chart trong [Spec 19 Chart](19-chart.md) Phase muộn.

## Acceptance criteria
N/A (out of scope).

Nếu implement Map Chart 2D:
1. Data: A=Country, B=Value → Insert → Map Chart → world map với country tô màu theo value.
2. Choropleth: gradient color scale.
3. No 3D, no animation.

## Phụ thuộc
- [19 Chart](19-chart.md) — Map Chart minimal.

## Risk
**Out of scope.** 3D Maps là một sub-product, không phải feature đơn lẻ.

## Phase
Out of scope Ezcel. Re-evaluate khi/nếu pivoting về geo-analytics niche.
