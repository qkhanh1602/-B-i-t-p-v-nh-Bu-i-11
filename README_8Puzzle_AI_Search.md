# 8-Puzzle Solver – AI Search Algorithms

## 1. Giới thiệu

Đây là project mô phỏng bài toán **8-Puzzle** bằng Python với giao diện đồ họa `tkinter`.  
Project hỗ trợ nhiều nhóm thuật toán tìm kiếm trong môn Trí tuệ nhân tạo, bao gồm:

- Tìm kiếm mù
- Tìm kiếm có thông tin
- Tìm kiếm cục bộ
- Tìm kiếm trong môi trường không chắc chắn bằng **belief state**

Chương trình cho phép người dùng nhập trạng thái bắt đầu, trạng thái mục tiêu, chọn thuật toán, chọn hàm đánh giá `g(n)`, `h(n)`, `h(B)`, xem quá trình chạy, xem Search Trace và quan sát từng bước di chuyển của bảng 8-Puzzle.

---

## 2. Chức năng chính

### 2.1. Nhập trạng thái 8-Puzzle

Người dùng có thể nhập:

- Initial state: trạng thái bắt đầu
- Goal state: trạng thái mục tiêu

Quy ước:

```text
0 là ô trống
```

Ví dụ:

```text
Initial state: 123406758
Goal state:    123456780
```

Tương ứng với ma trận:

```text
1 2 3
4 _ 6
7 5 8
```

---

## 3. Các thuật toán được hỗ trợ

### 3.1. Nhóm tìm kiếm mù

Các thuật toán tìm kiếm mù không sử dụng heuristic `h(n)` để dự đoán khoảng cách đến mục tiêu.

Project hỗ trợ:

```text
BFS Cách 1
BFS Cách 2
DFS
IDS
UCS
```

Trong đó:

- **BFS Cách 1**: kiểm tra child trước khi thêm vào frontier.
- **BFS Cách 2**: lấy node ra khỏi frontier rồi mới kiểm tra reached.
- **DFS**: dùng stack LIFO để đi sâu trước.
- **IDS**: lặp DFS với giới hạn độ sâu tăng dần.
- **UCS**: dùng Priority Queue theo chi phí `g(n)`.

Với UCS, người dùng có thể chọn cách tính `g(n)`:

```text
Số ô sai
Manhattan
Dãy ngược
Swap
```

---

### 3.2. Nhóm tìm kiếm có thông tin

Các thuật toán tìm kiếm có thông tin sử dụng heuristic để đánh giá trạng thái.

Project hỗ trợ:

```text
Greedy
A*
IDA*
```

Ý nghĩa:

- **Greedy**: chọn node có `h(n)` nhỏ nhất.
- **A***: chọn node có `f(n) = g(n) + h(n)` nhỏ nhất.
- **IDA***: kết hợp DFS giới hạn với ngưỡng `f(n)` tăng dần.

Với A* và IDA*, người dùng có thể chọn cả:

```text
g(n)
h(n)
```

Các hàm đánh giá hỗ trợ:

```text
Số ô sai
Manhattan
Dãy ngược
Swap
```

---

### 3.3. Nhóm tìm kiếm cục bộ

Project hỗ trợ các thuật toán Local Search:

```text
Leo đồi đơn giản
Leo núi dốc nhất
Leo núi ngẫu nhiên
Leo núi lặp lại ngẫu nhiên
Local Beam Search
Simulated Annealing
```

Ý nghĩa:

- **Leo đồi đơn giản**: gặp neighbor đầu tiên tốt hơn thì chọn.
- **Leo núi dốc nhất**: sinh tất cả neighbor, chọn neighbor có `h(n)` tốt nhất.
- **Leo núi ngẫu nhiên**: chọn ngẫu nhiên trong nhóm neighbor tốt hơn.
- **Leo núi lặp lại ngẫu nhiên**: chạy lại nhiều lần để tránh kẹt local optimum.
- **Local Beam Search**: giữ lại `k` trạng thái tốt nhất sau mỗi vòng.
- **Simulated Annealing**: có thể chấp nhận trạng thái xấu hơn theo xác suất để thoát local optimum.

Local Beam Search cho phép chọn:

```text
h(n)
Beam k
```

---

## 4. Môi trường không chắc chắn

Project có chế độ:

```text
Môi trường không chắc chắn
```

Trong chế độ này, agent không còn làm việc với một trạng thái bắt đầu duy nhất.  
Thay vào đó, agent làm việc với **belief state**.

```text
Belief state = tập các trạng thái có thể xảy ra
```

Ví dụ:

```text
Initial belief states:
123406758
123456708
123046758
```

Nghĩa là agent có thể đang ở một trong các trạng thái trên.

---

### 4.1. Goal Set

Trong môi trường không chắc chắn, người dùng có thể nhập một hoặc nhiều trạng thái mục tiêu:

```text
Goal belief states:
123456780
123456708
```

Nếu là môi trường không chắc chắn toàn phần, Goal không nhất thiết chỉ có một trạng thái duy nhất.  
Khi đó, ta xem tập Goal là **Goal Set**.

Một trạng thái được xem là đạt mục tiêu nếu nó thuộc Goal Set.

---

### 4.2. Điều kiện dừng

Trong môi trường không chắc chắn, thuật toán chỉ dừng khi:

```text
Tất cả trạng thái trong belief state đều thuộc Goal Set
```

Nếu chỉ có một trạng thái đạt Goal nhưng các trạng thái còn lại chưa đạt Goal thì thuật toán vẫn chưa dừng.

Ví dụ:

```text
B = {Goal, S2, S3}
```

Nếu `S2` hoặc `S3` chưa thuộc Goal Set thì belief state chưa hoàn thành.

---

### 4.3. Trạng thái hấp thụ

Project sử dụng quy ước:

```text
Nếu một state đã thuộc Goal Set thì giữ nguyên.
```

Nghĩa là:

```text
Action(Goal) = Goal
```

Điều này giúp các board đã đạt mục tiêu không bị phá ra khỏi Goal trong các bước tiếp theo.

---

### 4.4. Hiển thị nhiều board

Khi chạy môi trường không chắc chắn:

- Nhập bao nhiêu Initial belief states thì giao diện hiển thị bấy nhiêu bảng 8-Puzzle.
- Mỗi bảng được đánh số `S1`, `S2`, `S3`, ...
- Mỗi bước chạy sẽ cập nhật toàn bộ các board trong belief state.
- Nếu có 3 Start thì mỗi Step luôn thể hiện 3 board.

Ví dụ:

```text
S1 | S2 | S3
```

Điều này giúp dễ quan sát quá trình nhiều trạng thái cùng được xử lý song song.

---

## 5. Thuật toán trong môi trường không chắc chắn

Trong chế độ môi trường không chắc chắn, người dùng có thể chọn các thuật toán đã học để chạy trên belief state:

```text
BFS Cách 1
BFS Cách 2
UCS
Greedy
A*
IDA*
DFS
IDS
Leo đồi đơn giản
Leo núi dốc nhất
Leo núi ngẫu nhiên
Leo núi lặp lại ngẫu nhiên
Local Beam Search
Simulated Annealing
```

Điểm khác biệt:

```text
Node = belief state
```

Thay vì một node chỉ là một bảng 8-Puzzle, trong môi trường không chắc chắn một node là một tập nhiều bảng.

---

## 6. Cách tính heuristic cho belief state

Vì một belief state gồm nhiều trạng thái, nên mỗi trạng thái có thể có một giá trị heuristic riêng.

Ví dụ:

```text
B = {S1, S2, S3}

h(S1) = 2
h(S2) = 5
h(S3) = 3
```

Để tính heuristic chung cho belief state, project hỗ trợ hai cách:

### 6.1. Lấy giá trị lớn nhất

```text
h(B) = max(h(S1), h(S2), ..., h(Sn))
```

Ví dụ:

```text
h(B) = max(2, 5, 3) = 5
```

Cách này xem trạng thái xấu nhất là đại diện cho belief state.

---

### 6.2. Lấy giá trị trung bình

```text
h(B) = (h(S1) + h(S2) + ... + h(Sn)) / n
```

Ví dụ:

```text
h(B) = (2 + 5 + 3) / 3 = 3.33
```

Cách này đánh giá mức độ tốt trung bình của toàn bộ belief state.

---

### 6.3. Trường hợp bằng điểm

Nếu nhiều belief state có cùng giá trị `h(B)` hoặc cùng cost, chương trình có thể chọn ngẫu nhiên trong nhóm bằng điểm.

---

## 7. Search Trace

Project có bảng Search Trace để theo dõi quá trình thuật toán chạy.

Với thuật toán thông thường, Trace hiển thị:

```text
Node | Frontier | Reached
```

Với thuật toán Local Search, Trace hiển thị:

```text
Current Node | Next Node | Better Neighbors
```

Với môi trường không chắc chắn, Trace hiển thị:

```text
Current Belief State | Next Belief State | Candidate Beliefs
```

Điều này giúp phân biệt rõ cách thuật toán hoạt động ở từng nhóm.

---

## 8. Cách chạy chương trình

### 8.1. Yêu cầu

Máy cần có Python 3.

Thư viện sử dụng:

```text
tkinter
collections
heapq
random
math
time
```

Các thư viện này đều là thư viện chuẩn của Python.

---

### 8.2. Chạy file

Mở terminal hoặc CMD tại thư mục chứa file Python, sau đó chạy:

```bash
python 8puzzle_buoi10_LOCAL_BEAM_BELIEF_FULL_FIXED.py
```

Nếu máy dùng Python 3 riêng:

```bash
python3 8puzzle_buoi10_LOCAL_BEAM_BELIEF_FULL_FIXED.py
```

---

## 9. Hướng dẫn sử dụng giao diện

### Bước 1: Nhập trạng thái

Nhập Initial state và Goal state.

Ví dụ:

```text
Initial state: 123406758
Goal state:    123456780
```

### Bước 2: Chọn thuật toán

Chọn thuật toán trong ô Search algorithm.

### Bước 3: Chọn g(n), h(n), Beam k nếu cần

Tùy thuật toán, giao diện sẽ tự động hiện các ô cần thiết:

- UCS hiện `g(n)`
- Greedy hiện `h(n)`
- A* và IDA* hiện `g(n)` và `h(n)`
- Local Beam hiện `h(n)` và `Beam k`
- Môi trường không chắc chắn hiện panel riêng cho belief state

### Bước 4: Bấm Solve Puzzle

Chương trình sẽ chạy thuật toán và hiển thị:

- Runtime
- Nodes expanded
- Search depth
- Path cost
- Path
- Search Trace
- Animation các bước

---

## 10. Ví dụ nhập môi trường không chắc chắn

Chọn:

```text
Search algorithm: Môi trường không chắc chắn
```

Nhập:

```text
Initial belief states:
123406758
123456708
123046758
```

Nhập:

```text
Goal belief states:
123456780
```

Chọn thuật toán chạy belief state, ví dụ:

```text
Local Beam Search
```

Chọn:

```text
h(B): Manhattan
Cách tính h(B): MAX
Beam k: 2
```

Sau đó bấm:

```text
Solve Puzzle
```

Chương trình sẽ chạy nhiều board cùng lúc và chỉ dừng khi tất cả board đều đạt Goal.

---

## 11. Ghi chú quan trọng

- `0` đại diện cho ô trống.
- State phải gồm đủ các số từ `0` đến `8`, không lặp.
- Với 8-Puzzle thông thường, chương trình kiểm tra tính giải được bằng inversion.
- Với môi trường không chắc chắn, mỗi dòng trong Initial belief states là một Start có thể xảy ra.
- Local Search có thể bị kẹt tại local optimum.
- Simulated Annealing có thể chấp nhận trạng thái xấu hơn theo xác suất.
- Belief Search chỉ hoàn thành khi tất cả state trong belief state thuộc Goal Set.

---

## 12. Tóm tắt

Project này giúp mô phỏng trực quan các thuật toán tìm kiếm trong AI trên bài toán 8-Puzzle.  
Ngoài các thuật toán cơ bản như BFS, DFS, UCS, Greedy, A*, IDA*, project còn hỗ trợ các thuật toán Local Search và môi trường không chắc chắn bằng belief state.

Điểm nổi bật của project:

```text
Có giao diện trực quan
Có animation từng bước
Có Search Trace
Có chọn g(n), h(n), h(B)
Có mô phỏng môi trường không chắc chắn bằng nhiều board
Có Local Beam Search, Simulated Annealing và các biến thể Hill Climbing
```
