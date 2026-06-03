# Hướng dẫn import KML vào Google My Maps

Hai cấp bản đồ: **BẢN ĐỒ TỔNG** (toàn vùng) và **BẢN ĐỒ CON** (chi tiết từng cung).

## 1. BẢN ĐỒ TỔNG — điểm đến + tuyến tổng quan

Tạo 1 My Map, import từng file thành 1 layer (My Maps tối đa 10 layer/map):

**6 layer điểm đến** (`diem-den/`) — mỗi điểm có giới thiệu thật + dịch vụ/SĐT:
- `di-tich-tam-linh.kml` — chùa, đình, đền, nhà thờ (9 điểm)
- `canh-quan-thien-nhien.kml` — hồ, thung, hang, đồi hoa, đường tràm (7 điểm)
- `am-thuc.kml` — F&B, điểm dừng chân, chợ (5 điểm)
- `luu-tru.kml` — homestay / farmstay (6 điểm)
- `trai-nghiem-nghe.kml` — mò trai, vườn, đầm sen, nông trại, dược liệu (9 điểm)
- `di-san-phi-vat-the.kml` — ICH (Mo Mường, cồng chiêng, dệt…) + không gian văn hoá (16 điểm)

**Tuyến tổng** (`tuyen/`): import 19 file LineString nếu cần overlay tuyến lên map tổng (vượt 10 layer → tách thành map thứ 2 hoặc dùng bản đồ con bên dưới).

## 2. BẢN ĐỒ CON — chi tiết từng cung (`cung-chi-tiet/`)

19 file, **mỗi file = 1 My Map riêng** cho 1 cung. Mỗi file gồm:
- 1 LineString tuyến (màu theo loại).
- Marker đánh số `1. … 2. …` cho mỗi điểm dừng, popup = giờ + giới thiệu điểm + lưu ý.

**Màu tuyến theo loại:**
- Xe đạp → xanh lá · Tour → cam · Trek → đỏ

### ⚠️ Lưu ý cung xe đạp
LineString bám đường dân sinh từ khảo sát. Nếu định tuyến OSRM lệch (đặc biệt đoạn đường HCM), **kéo lại tay** theo đường thực địa trong My Maps.

### Điểm dừng "hoạt động" không có marker
8 stop là hoạt động không gắn địa điểm cố định (vd "Giao lưu chia tay", "Nghỉ giữa rừng", "Bữa trưa dã ngoại") → đã bỏ marker, nội dung nằm trong mô tả tuyến/itinerary. Số thứ tự marker giữ nguyên theo lịch trình nên có thể nhảy số (vd …5, 7) — đúng dự kiến.

## Cách import (My Maps)
1. Tạo bản đồ mới → "Thêm lớp" → "Nhập" → chọn file `.kml`.
2. Đặt tên lớp, chọn style "Nhóm theo phong cách thống nhất" để giữ icon/màu.
3. Marker thiếu/sai vị trí (toạ độ TẠM) → kéo trực tiếp trên map.

## Điểm còn toạ độ TẠM (cần kéo lại thực địa)
- Đình Phú Cốc, Thung Cấm, Con đường Tràm, Rừng Tràm (Đồng Văn)
- Gió Núi Farmstay, Chợ Mới An Phú, Vườn Hoa Núi
- Sản vật núi rừng (anh Tiến), Rượu Tám Lập (Đồi Lý), Nhà văn hoá dân tộc (thôn Đình)
- Các ICH ở anchor Đồi Dùng (di sản phi vật thể, không gắn điểm cố định)
