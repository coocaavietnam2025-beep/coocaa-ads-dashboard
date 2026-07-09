# Meta Ads Dashboard — TV Khung Tranh Coocaa

Dashboard tĩnh (index.html) đọc dữ liệu từ `data.json`, được một GitHub Action
tự động cập nhật mỗi ngày bằng cách gọi thẳng Meta Marketing API. Không cần
server, không cần Cowork — chỉ cần GitHub.

## Cấu trúc

```
github-dashboard/
├── index.html                      # Dashboard (VI/EN/ZH), đọc data.json
├── data.json                       # Dữ liệu mới nhất (Action tự cập nhật)
├── scripts/fetch_data.py           # Script gọi Meta Graph API
└── .github/workflows/update-data.yml  # Chạy fetch_data.py mỗi ngày
```

## Cài đặt (làm 1 lần)

### 1. Tạo repo và đẩy code lên
Tạo repo GitHub mới (ví dụ `coocaa-ads-dashboard`), copy toàn bộ nội dung
trong thư mục `github-dashboard/` này vào repo (giữ nguyên cấu trúc thư mục,
kể cả `.github/workflows/`), rồi commit + push lên `main`.

### 2. Tạo Meta System User Access Token
Access token gắn với tài khoản cá nhân sẽ hết hạn — nên dùng **System User
Token** (không hết hạn) để Action chạy ổn định lâu dài:

1. Vào **Meta Business Settings** → **Users** → **System Users** → tạo System
   User mới (vai trò Employee/Admin đều được).
2. Bấm **Add Assets** → chọn Ad Account `act_1623969776402359` → cấp quyền
   **View Performance** (tối thiểu, chỉ cần đọc dữ liệu).
3. Bấm **Generate New Token** → chọn app quảng cáo đang dùng → tick quyền
   `ads_read` → Generate. Copy token này lại (chỉ hiện 1 lần).

### 3. Khai báo Secrets & Variables trong repo GitHub
Vào repo → **Settings** → **Secrets and variables** → **Actions**:

- **Secrets** (giá trị nhạy cảm, không log ra):
  - `META_ACCESS_TOKEN` = token vừa tạo ở bước 2
  - `AD_ACCOUNT_ID` = `1623969776402359`
- **Variables** (không nhạy cảm):
  - `CAMPAIGN_ID` = `120246939599090259`

### 4. Bật quyền ghi cho Action
Vào **Settings** → **Actions** → **General** → mục **Workflow permissions**,
chọn **Read and write permissions** → Save. (Cần để Action tự commit
`data.json` mỗi ngày.)

### 5. Bật GitHub Pages
Vào **Settings** → **Pages** → **Source**: chọn **Deploy from a branch** →
**Branch**: `main` / `(root)` → Save.

### 6. Chạy thử lần đầu
Vào tab **Actions** → chọn workflow **Update Meta Ads Dashboard Data** →
**Run workflow** để tạo `data.json` thật ngay (không cần chờ đến giờ cron).

Sau vài phút, dashboard sẽ có tại:
`https://<username>.github.io/<ten-repo>/`

## Lịch chạy tự động

Mặc định workflow chạy **23:00 UTC mỗi ngày** (≈ 06:00 sáng giờ Việt Nam hôm
sau). Muốn đổi giờ, sửa dòng `cron:` trong
`.github/workflows/update-data.yml` (cú pháp cron chuẩn, theo giờ UTC).

## Ghi chú

- Script `fetch_data.py` chỉ dùng thư viện chuẩn của Python (`urllib`), không
  cần cài thêm gói gì trong Action.
- `data.json` được thêm vào Git nên bạn có luôn lịch sử số liệu theo ngày qua
  các commit — có thể dùng để dựng biểu đồ dài hạn sau này nếu muốn.
- Nếu access token hết hạn hoặc bị thu hồi quyền, Action sẽ báo lỗi đỏ trong
  tab Actions — vào tạo lại token ở bước 2 và cập nhật lại Secret.
