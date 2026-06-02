# SPEC 28 — What-If Analysis (Goal Seek / Scenario Manager / Data Table / Solver)

## Mục tiêu
Data → What-If Analysis dropdown: Goal Seek, Scenario Manager, Data Table. Cộng thêm Solver (Add-in).

## Trạng thái hiện tại
- ✗ Chưa có.

## 28.1 Goal Seek

Tìm giá trị input để công thức ra kết quả mong muốn.

### Dialog (Data → What-If Analysis → Goal Seek)
- **Set cell**: ô chứa công thức (vd C10 chứa `=A10*B10`).
- **To value**: giá trị muốn đạt (vd 1000).
- **By changing cell**: ô input (vd B10).

### Engine
- Iterative root-finding: bisection / Newton-Raphson / secant method.
- Stop khi |result - target| < tolerance hoặc đạt max iterations (mặc định 100, từ Calculation Options).

### Result
- Dialog kết quả: "Goal Seeking with Cell C10 found a solution. Target value: 1000. Current value: 999.998. [OK][Cancel]"
- OK → giữ thay đổi. Cancel → khôi phục.

## 28.2 Scenario Manager

Quản lý nhiều bộ giá trị input cho cùng công thức.

### Dialog
- List scenarios.
- **Add**: name + Changing cells + Values cho từng cell.
- **Edit / Delete / Merge / Summary**.
- **Show**: áp scenario lên sheet.

### Summary report
- Create Scenario Summary → sheet mới với bảng comparison: cột = scenarios; rows = changing cells + result cells.

## 28.3 Data Table

Tính ma trận kết quả khi 1 hoặc 2 input thay đổi.

### One-variable data table
- Setup:
  - C1 = formula `=A1*B1`
  - Cột B = list giá trị thử cho A1
  - Chọn B1:C[n+1]
- Data → What-If → Data Table → "Column input cell" = A1 → OK.
- Result: cột C lấp đầy với formula áp giá trị B tương ứng vào A1.

### Two-variable data table
- Setup:
  - B1 = formula
  - Cột A = list 1 input
  - Row 1 = list input khác
- Chọn cả block → Data Table → 2 input cells.
- Result: ma trận.

### Implementation
- Array formula `{=TABLE(row_input, col_input)}` — special internal formula của Excel.
- Recompute toàn ma trận khi data đổi.

## 28.4 Solver (Add-in)

Optimization solver: tìm input → tối đa/tối thiểu/equal target value, với constraints.

### Dialog
- **Set objective**: ô objective cell.
- **To**: Max / Min / Value Of [N].
- **By changing variable cells**: list cells.
- **Subject to the Constraints**:
  - Add → cell + operator (<=, >=, =, int, bin, dif) + value.
- **Solving method**:
  - **GRG Nonlinear**: smooth nonlinear problems.
  - **Simplex LP**: linear problems.
  - **Evolutionary**: non-smooth.
- **Options**: precision, tolerance, max time, max iterations.
- **Solve** → result dialog: Keep Solution / Restore Original Values; Save Scenario; Reports (Answer / Sensitivity / Limits).

### Implementation
- Phase muộn. Dùng `scipy.optimize` (cần add dependency):
  - `scipy.optimize.minimize` (GRG, Powell, BFGS) cho nonlinear.
  - `scipy.optimize.linprog` cho LP.
  - `scipy.optimize.differential_evolution` cho evolutionary.
- Constraints map sang scipy format.
- Solver UI có thể tách thành plugin (Add-in style — [Spec 41](41-add-ins-office-scripts.md) nếu có).

## Iterative Calculation Setting

(File → Options → Formulas → Calculation options)
- **Enable iterative calculation** checkbox: cho phép circular reference.
- Max iterations (default 100).
- Max change (default 0.001) — convergence threshold.

Liên quan: Goal Seek, Solver, công thức tự tham chiếu.

## Acceptance criteria

### Goal Seek
1. B1=5, B2=3, B3=`=B1*B2` (= 15). Goal Seek Set B3 → To 20 → By changing B1 → kết quả B1 ≈ 6.667.

### Scenario Manager
2. Add 3 scenarios "Best/Likely/Worst" cho B1,B2; Show từng cái → giá trị thay đổi tương ứng.
3. Summary → sheet mới với bảng comparison 3 scenarios.

### Data Table
4. Setup one-variable: A1=growth rate, A10=`=A1*1000`. Cột B1:B6 = 0.05, 0.10, 0.15, 0.20, 0.25. Chọn A10:B16, Data Table column input = A1 → cột B11:B16 hiển thị 50, 100, 150, 200, 250.

### Solver
5. Linear: max objective = A1*5 + B1*3, s.t. A1+B1 <= 10, A1 >= 0, B1 >= 0 → solver tìm A1=10, B1=0.

## Phụ thuộc
- [12 Formula System](12-formula-system.md) — engine.
- scipy (Solver) — optional dependency.

## Risk
- Solver: dependency lớn, có thể wrap thành plugin.
- Data Table với 2 variables: cần special formula type `{=TABLE(r, c)}`.
- Iterative calc với circular ref dễ gây vòng lặp vô tận → giới hạn cứng.
