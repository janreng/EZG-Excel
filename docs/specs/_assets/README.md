# Assets / Reference Images

Folder chứa ảnh ref cho specs — chủ yếu để **bot-main (slave) khi code có ref visual** chứ không phải đoán.

## Tổ chức

```
_assets/
├── screenshots/        # Ảnh chụp Excel thật (Windows 11, Mac)
│   ├── excel-start-screen.png
│   ├── excel-backstage-info.png
│   ├── excel-ribbon-home.png
│   ├── excel-format-cells-dialog.png
│   ├── excel-name-box-edit.png
│   └── ...
├── icons/              # Fluent UI icons (SVG, copy từ Microsoft repo)
│   ├── fluent-bold.svg
│   ├── fluent-italic.svg
│   └── ...
└── mockups/            # ASCII / Figma mockup cho UI mới Ezcel-specific
    ├── ezcel-home-screen.png
    └── ...
```

## Cách bổ sung

### Screenshots Excel thật
1. Mở Excel 365 trên Windows 11.
2. Chụp dialog/feature cần (Win+Shift+S → Screen Snip).
3. Crop sao cho rõ component cần ref + bao quanh đủ context (10-20px viền).
4. Save PNG vào `screenshots/` với tên `excel-<feature>-<state>.png`.
   - vd `excel-cf-data-bars-blue.png`, `excel-formula-bar-edit-mode.png`.
5. Reference trong spec markdown:
   ```markdown
   ![Format Cells dialog - Number tab](./_assets/screenshots/excel-format-cells-number.png)
   ```

### Fluent UI Icons
1. Download SVG từ https://github.com/microsoft/fluentui-system-icons/tree/main/assets
2. Copy SVG files cần dùng vào `icons/`.
3. Rename theo convention: `fluent-<name>-<style>-<size>.svg` (vd `fluent-bold-regular-20.svg`).

### Mockups
- Ezcel-specific UI (không phải clone Excel 1:1) — tạo bằng Figma / Excalidraw → export PNG.
- Hoặc ASCII mockup trong spec markdown trực tiếp (đã làm với [Spec 51](../51-start-screen-backstage.md)).

## Quy ước file naming

- Lowercase, kebab-case: `excel-format-cells-dialog.png`
- Có state: `-default`, `-hover`, `-active`, `-disabled`.
- Có theme: `-light`, `-dark` nếu có 2 versions.
- Resolution: minimum 1920×1080 source; có thể resize nhỏ trong markdown.

## License

⚠ Screenshots Excel có thể chịu Microsoft copyright. Chỉ dùng nội bộ (`docs/`), KHÔNG commit lên public repo nếu repo public.

Fluent UI Icons: **MIT License** (Microsoft open-source) → OK commit.

## Hiện trạng

**Trống.** Boss cần download ảnh thực và bỏ vào folder này — em (assistant) không thể tự download ảnh Excel screenshot. Boss có 2 cách:
1. Tự screenshot Excel thật rồi copy vào.
2. Bảo Slave (bot-main code) tự pull từ Microsoft Learn / techcommunity URLs trong specs.

Reference URLs đã có trong:
- [Spec 50](../50-design-system.md) §50.10 — Microsoft Learn, Fluent UI.
- [Spec 51](../51-start-screen-backstage.md) §51.5 — Start Screen + Backstage screenshots links.
