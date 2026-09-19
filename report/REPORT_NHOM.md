# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [Tên nhóm]
**Thành viên:** Hồ Đăng Phúc
**Ngày:** 19/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Học bổng và hỗ trợ tài chính dành cho người học tại Trường Đại học Khoa học và Công nghệ Hà Nội (USTH).

**Tại sao nhóm chọn chủ đề này?**
> Bộ tài liệu tập hợp các quy định, tiêu chí, giá trị, hồ sơ, quy trình và thời hạn học bổng từ các nguồn công khai của USTH. Phạm vi này phù hợp để xây dựng hệ thống truy xuất vì người học thường cần đối chiếu thông tin cụ thể giữa nhiều loại học bổng và năm học khác nhau.

**Mô tả corpus:** Corpus gồm đúng 8 tài liệu Markdown: 5 tài liệu tiếng Anh và 3 tài liệu tiếng Việt, được lấy ngày 2026-09-19. Nội dung bao phủ quy định chung, thông báo nộp hồ sơ, quy trình, học bổng Vallet, học bổng cho sinh viên hiện tại, chương trình Green Tech, hỗ trợ tài chính và các đợt đang hiển thị trên cổng học bổng. Nguồn tuyển sinh tiến sĩ bị chặn bởi `robots.txt` không được đưa vào corpus.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự (không tính frontmatter) | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Regulations on Scholarship for USTH Students | https://usth.edu.vn/en/regulations-on-scholarship-for-usth-students-11708/ | 2026-09-19 / 177-QD-DHKHCNHN-2026 | 1328 | `audience: student`; `department: student-affairs`; `category: scholarship-regulation`; `language: en` |
| 2 | Scholarship Application Submission 2026-2027 Wave 1 | https://usth.edu.vn/en/announcement-on-scholarship-application-submission-academic-year-2026-2027-wave-1-12694/ | 2026-09-19 / 2026-2027 | 3213 | `audience: student`; `department: student-affairs`; `category: application`; `language: en` |
| 3 | Procedures for Scholarships and Financial Aids Support | https://usth.edu.vn/en/procedures-for-scholarships-and-financial-aids-support-3632/ | 2026-09-19 / not-stated | 1173 | `audience: all`; `department: student-affairs`; `category: procedure`; `language: en` |
| 4 | Vallet Scholarship Program 2026 for Northern Students | https://usth.edu.vn/thong-bao-trien-khai-chuong-trinh-hoc-bong-vallet-nam-2026-danh-cho-sinh-vien-khu-vuc-mien-bac-31432/ | 2026-09-19 / 01-2026-TB-HBSVMB | 6001 | `audience: student`; `department: student-affairs`; `category: external-scholarship`; `language: vi` |
| 5 | Scholarship Application for Current Vietnamese Students 2025-2026 | https://usth.edu.vn/tiep-nhan-ho-so-dang-ky-hoc-bong-nam-hoc-2025-2026-danh-cho-sinh-vien-hoc-vien-viet-nam-dang-hoc-tai-truong-26801/ | 2026-09-19 / 536-QD-KHCN-2025 | 4393 | `audience: student`; `department: student-affairs`; `category: current-student-scholarship`; `language: vi` |
| 6 | Green Tech Scholarship and Internship 2026 | https://usth.edu.vn/en/green-tech-scholarship-internship-2026-11897/ | 2026-09-19 / not-stated | 861 | `audience: student`; `department: student-affairs`; `category: external-scholarship`; `language: en` |
| 7 | Financial Aid for Students in Difficult Circumstances 2024-2025 | https://usth.edu.vn/en/financial-aid-award-ceremony-for-students-in-difficult-circumstances-academic-year-2024-2025-12301/ | 2026-09-19 / 2024-2025 | 4635 | `audience: student`; `department: student-affairs`; `category: financial-aid`; `language: en` |
| 8 | USTH Student Scholarship Portal 2026-2027 | https://erp.usth.edu.vn/students | 2026-09-19 / 2026-2027 | 472 | `audience: student`; `department: student-affairs`; `category: scholarship-portal`; `language: vi` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc `not-stated` khi nguồn không nêu phiên bản) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `usth-scholarship-regulation-2026` | Định danh duy nhất tài liệu và đối chiếu kết quả với tệp nguồn. |
| `title` | string | `Regulations on Scholarship for USTH Students` | Hiển thị và xếp hạng kết quả theo tên tài liệu. |
| `source_url` | URL | `https://usth.edu.vn/en/regulations-on-scholarship-for-usth-students-11708/` | Truy vết và kiểm chứng nội dung từ nguồn gốc. |
| `retrieved_at` | date (`YYYY-MM-DD`) | `2026-09-19` | Xác định thời điểm thu thập khi đánh giá độ mới của dữ liệu. |
| `document_version` | string | `177-QD-DHKHCNHN-2026` | Phân biệt quy định theo số hiệu/phiên bản; dùng `not-stated` khi nguồn không nêu. |
| `audience` | enum (`student`, `faculty`, `staff`, `all`) | `student` | Cho phép lọc tài liệu theo đối tượng. |
| `department` | string | `student-affairs` | Giới hạn truy xuất theo đơn vị phụ trách. |
| `category` | string | `application` | Lọc theo loại nội dung như thông báo nộp hồ sơ, quy định hay quy trình. |
| `language` | string | `en` | Lọc theo ngôn ngữ của tài liệu. |
| `license_or_permission` | string | `public-source` | Ghi nhận căn cứ sử dụng và hỗ trợ kiểm tra quản trị dữ liệu. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare(text, chunk_size=500)` trên 3 tài liệu đại diện (đã bỏ frontmatter YAML trước khi đo), cộng thêm `HeadingChunker` (chiến lược của R3) để so sánh:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `usth-scholarship-regulation-2026.md` (1325 ký tự) | FixedSizeChunker (`fixed_size`) | 3 | 475.0 | Không — cắt cứng theo ký tự, có thể chia đôi giữa câu |
| `usth-scholarship-regulation-2026.md` | SentenceChunker (`by_sentences`) | 2 | 660.5 | Có, nhưng chunk khá dài vì gộp 3 câu/nhóm |
| `usth-scholarship-regulation-2026.md` | RecursiveChunker (`recursive`) | 3 | 440.3 | Có — ưu tiên tách theo đoạn/câu trước khi cắt cứng |
| `usth-scholarship-regulation-2026.md` | HeadingChunker (`heading`, R3) | 3 | 440.3 | Tốt nhất — mỗi chunk trùng khớp một mục quy định |
| `usth-vallet-scholarship-2026.md` (5997 ký tự) | FixedSizeChunker | 14 | 474.8 | Không |
| `usth-vallet-scholarship-2026.md` | SentenceChunker | 13 | 458.7 | Có |
| `usth-vallet-scholarship-2026.md` | RecursiveChunker | 14 | 426.5 | Có |
| `usth-vallet-scholarship-2026.md` | HeadingChunker (R3) | 14 | 414.6 | Tốt nhất — tách đúng theo `## I.`, `## II.`, ... |
| `usth-scholarship-procedure.md` (1170 ký tự) | FixedSizeChunker | 3 | 423.3 | Không |
| `usth-scholarship-procedure.md` | SentenceChunker | 3 | 387.7 | Có |
| `usth-scholarship-procedure.md` | RecursiveChunker | 3 | 388.7 | Có |
| `usth-scholarship-procedure.md` | HeadingChunker (R3) | 3 | 388.7 | Tương đương recursive vì tài liệu ngắn, ít heading |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — Hồ Đăng Phúc (R3 · Strategy)**
- **Loại chiến lược:** custom — `HeadingChunker` (chunk theo heading Markdown)
- **Mô tả & lý do chọn cho chủ đề này:** Các tài liệu học bổng USTH đều được biên soạn theo mục (`## I. Thông Tin Chung`, `## II. Đối Tượng...`), mỗi mục là một đơn vị ngữ nghĩa trọn vẹn do người soạn chia sẵn. Thay vì cắt cứng theo số ký tự hay số câu, `HeadingChunker` tách văn bản tại từng dòng heading rồi hạ các mục quá dài xuống `RecursiveChunker`, giữ nguyên heading ở đầu mỗi mảnh con để không chunk nào mất ngữ cảnh "đang thuộc mục nào" (ví dụ mục V "Phương Pháp Thẩm Định" của Vallet dài hơn 500 ký tự vẫn giữ được tiêu đề khi bị chia nhỏ tiếp).
- **Code snippet (nếu custom):**
```python
class HeadingChunker:
    HEADING_RE = re.compile(r"^#{2,3}\s+.+$", re.MULTILINE)

    def chunk(self, text: str) -> list[str]:
        headings = list(self.HEADING_RE.finditer(text))
        if len(headings) < 2:
            return RecursiveChunker(chunk_size=self.chunk_size).chunk(text)
        # tách theo từng heading -> section; section dài quá chunk_size
        # được hạ xuống RecursiveChunker, heading được lặp lại ở mỗi mảnh con
        ...
```
(mã đầy đủ tại [src/chunking.py](../src/chunking.py))

**Thành viên 2 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

**Thành viên 3 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Hồ Đăng Phúc (R3) | HeadingChunker (phẳng) | 3/5 câu khớp gold marker với `OpenAIEmbedder` thật (xem `REPORT_CANHAN.md` mục 5) | Chunk trùng khớp ranh giới ngữ nghĩa của văn bản quy định (mỗi mục là một chunk), không cắt giữa câu/mục | Với văn bản ngắn/ít heading (VD `usth-scholarship-procedure.md`), kết quả rơi về giống hệt `RecursiveChunker`; một số heading dùng chung ngôn ngữ ("quy trình/thời hạn học bổng") giữa nhiều chương trình khác nhau nên vẫn bị nhầm chunk giữa các tài liệu |
| Hồ Đăng Phúc (R3, thử nghiệm mở rộng) | HeadingChunker + Hierarchical roll-up (RAPTOR-style, `src/hierarchical.py`) | 4/5 câu khớp gold marker (`summary_beam=3`), chạy trên Chroma persist dir riêng `./chroma_data/hierarchical_r3` (xem `REPORT_CANHAN.md` mục 5) | Tầng tóm tắt LLM gộp đúng các chunk cùng chủ đề trước khi drill-down, sửa được lỗi "nhầm chương trình học bổng" mà bản phẳng gặp phải ở câu 2 (Green Tech) | Tốn thêm ~15 lệnh gọi LLM tóm tắt (8 tài liệu, 58 chunk gốc); nới beam ở tầng tóm tắt để cứu câu 3 (quy trình) thực tế làm **giảm** xuống 3/5 vì phá vỡ lợi thế "khoanh vùng chủ đề" — xác nhận đây là đánh đổi recall/precision thật, không phải bug đơn giản có thể sửa một chiều |
| _(điền — R1/R2/Report Lead)_ | | | | |
| _(điền)_ | | | | |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Sau khi cả nhóm chuyển sang `OpenAIEmbedder` (`text-embedding-3-small`) thật, `RecursiveChunker` của nhóm đạt 4/5 câu khớp gold marker trong top-3, cao hơn `HeadingChunker` phẳng cá nhân (3/5) nhưng bằng đúng kết quả khi R3 thêm tầng roll-up hierarchical lên trên HeadingChunker (cũng 4/5). Với bộ dữ liệu học bổng USTH (mỗi tài liệu ngắn, 500–6000 ký tự, chưa đủ dài để một mục vượt xa `chunk_size=500`), lợi thế "chunk theo ranh giới ngữ nghĩa" của `HeadingChunker` phẳng không tạo khác biệt lớn so với `RecursiveChunker` — ranh giới quyết định retrieval đúng/sai chủ yếu nằm ở embedding model, không phải ở chiến lược chunk. Tuy nhiên khi ghép `HeadingChunker` với một tầng tóm tắt LLM (roll-up), chính "ranh giới sạch theo heading" ở tầng gốc lại giúp bản tóm tắt gom đúng chủ đề trước khi drill-down, kéo kết quả lên ngang `RecursiveChunker` — cho thấy hierarchical chunking là một cách nâng cấp hợp lý cho `HeadingChunker` nếu chấp nhận đánh đổi thêm chi phí gọi LLM.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Học bổng Green Tech 2026 có bao nhiêu suất, giá trị bao nhiêu và kéo dài bao lâu? | 04 suất, VND 18,000,000, kéo dài 6 tháng | `usth-green-tech-scholarship-2026` (mục "Scholarship Value") |
| 2 | Hạn cuối nộp hồ sơ Green Tech 2026 là ngày nào và dự kiến bắt đầu khi nào? | Hạn nộp 23/03/2026 (March 23, 2026), dự kiến bắt đầu tháng 4/2026 (April 2026) | `usth-green-tech-scholarship-2026` (mục thời hạn/lịch trình) |
| 3 | Quy trình xét học bổng và hỗ trợ tài chính của USTH gồm những bước nào? | Gồm Step 1, Step 2, Step 3 (nộp hồ sơ → lập danh sách đề cử/hội đồng → ra quyết định) | `usth-scholarship-procedure` (các mục "Step 1/2/3") |
| 4 | Trong năm học 2026-2027, USTH dự kiến dành bao nhiêu tiền cho quỹ học bổng và áp dụng cho nhóm nào? | VND 16 tỷ (16 billion), áp dụng cho sinh viên đại học (undergraduate) | `usth-scholarship-application-2026` |
| 5 | Đối tượng sinh viên nào được áp dụng các quy định học bổng năm 2026 của USTH? (**cần** `metadata_filter={"audience": "student"}` vì không lọc sẽ lẫn cả quy trình dành cho `audience: all`) | Áp dụng cho cả sinh viên Việt Nam (Vietnamese students) và sinh viên quốc tế (international students) | `usth-scholarship-regulation-2026` |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

> Kết quả dưới đây chạy bằng `benchmark/bench.py` (RecursiveChunker, `EmbeddingStore` in-memory) với **embedding thật** (`OpenAIEmbedder`, `text-embedding-3-small`) sau khi sửa lỗi khai báo `.env` (`EMBEDDING_PROVIDER` thay vì `EMBEDDING_PROVIDER_ENV`, khiến trước đó mọi script âm thầm rơi về `_mock_embed`).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Số suất & giá trị Green Tech | RecursiveChunker | **Có** (top-1 đúng `usth-green-tech-scholarship-2026`, khớp cả 2 gold marker) | HeadingChunker (R3) trượt câu này — top-3 toàn Vallet/current-student |
| 2 | Mốc thời gian Green Tech | RecursiveChunker | **Có** (top-1 và top-2 đều là `usth-green-tech-scholarship-2026`, khớp cả 2 mốc) | HeadingChunker (R3) chỉ đúng chủ đề "thời hạn" nhưng sai chương trình |
| 3 | Quy trình xét học bổng | RecursiveChunker ≈ HeadingChunker | Có, nhưng chỉ 1/3 gold marker | Cả hai chiến lược đều đưa `usth-scholarship-procedure` vào top-3 nhưng không đứng hạng 1, chỉ khớp "Step 1" |
| 4 | Quỹ học bổng 2026-2027 | RecursiveChunker ≈ HeadingChunker | **Có** (top-1 đúng `usth-scholarship-application-2026`, khớp đủ 2 gold marker) | Cả 2 chiến lược đều trả lời đúng câu này |
| 5 | Đối tượng quy định 2026 (có filter `audience: student`) | HeadingChunker (R3) | Không với RecursiveChunker (top-3 lẫn `usth-scholarship-portal-2026-2027`/Vallet), **có** với HeadingChunker (top-3 chứa đúng `usth-scholarship-regulation-2026`, khớp đủ 2 gold marker) | Câu duy nhất HeadingChunker thắng RecursiveChunker |

**Nhận định của R3 (Strategy):** Sau khi bật embedding thật, `RecursiveChunker` đạt 4/5, `HeadingChunker` đạt 3/5 — chênh lệch không lớn và mỗi chiến lược thắng ở câu khác nhau (Q1/Q2 recursive thắng, Q5 heading thắng). Kết luận: với corpus tài liệu ngắn như học bổng USTH, **embedding model** quyết định phần lớn chất lượng truy xuất (so với lúc dùng `_mock_embed`, cả 2 chiến lược đều nhảy từ ~1/5 lên 3-4/5); chiến lược chunking chỉ tạo khác biệt biên ở những câu mà nội dung liên quan bị "lẫn" giữa nhiều tài liệu cùng chủ đề (VD nhiều chương trình học bổng cùng nói về "quy trình"/"thời hạn").

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Có, rõ nhất ở câu 5: với embedding thật, chạy **không filter** trả về top-1 là `usth-scholarship-portal-2026-2027` (không đúng gold doc), trong khi chạy **có filter** `audience: student` bằng `HeadingChunker` lại đưa đúng `usth-scholarship-regulation-2026` vào top-3 và khớp đủ 2 gold marker. So sánh A/B trong `benchmark/bench.py` xác nhận `search_with_filter` lọc đúng cơ chế (loại `audience: all`/`PhD` trước khi tính điểm), và ở câu này việc lọc metadata tạo ra khác biệt thật giữa "có liên quan" và "không" — không chỉ đổi thứ tự nhẹ như khi còn dùng `_mock_embed`.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> - (R3) Chuyển từ `_mock_embed` sang `OpenAIEmbedder` thật (`text-embedding-3-small`) làm điểm truy xuất nhảy vọt: cả `RecursiveChunker` (nhóm) và `HeadingChunker` (R3) đều đi từ ~1/5 câu khớp gold marker lên 3-4/5, chứng minh bằng số liệu rằng chất lượng embedding quan trọng hơn nhiều so với lựa chọn chiến lược chunking trên corpus này.
> - (R3) `HeadingChunker` giữ ranh giới ngữ nghĩa tốt (mỗi mục quy định = một chunk) nhưng không phải lúc nào cũng thắng `RecursiveChunker`: ở 2/5 câu (Green Tech), `RecursiveChunker` thắng vì gom được đoạn liên tục chứa cả số liệu lẫn ngữ cảnh; ở câu cần lọc metadata (Q5), `HeadingChunker` lại thắng vì chunk theo mục giữ nguyên cụm "đối tượng áp dụng" liền với heading gốc.
> - _(điền thêm — Report & Demo Lead tổng hợp cùng R1/R2)_

**Công cụ demo:** toàn bộ 4 chiến lược chunking phẳng (Fixed/Sentence/Recursive/Heading) chạy trực tiếp trên trình duyệt (không cần server/API key), cộng với bảng kết quả benchmark thật (RecursiveChunker vs. HeadingChunker vs. Hierarchical roll-up) đã được đóng gói vào [`chunking_demo.html`](../chunking_demo.html) — mở file này bằng trình duyệt bất kỳ để trình chiếu khi thuyết trình, có thể đổi tài liệu mẫu/tham số ngay trên giao diện.

**Bài học rút ra khi so sánh trong nhóm:**
> Trên cùng một bộ tài liệu, `FixedSizeChunker` luôn cho nhiều chunk nhất và dễ cắt ngang câu/mục nhất (thấy rõ khi demo trực tiếp trên `chunking_demo.html`), trong khi `RecursiveChunker` và `HeadingChunker` cho số chunk gần bằng nhau và đều giữ ngữ cảnh tốt hơn hẳn — khác biệt giữa hai chiến lược này chỉ lộ ra khi *retrieval* thật sự chạy: `HeadingChunker` thắng khi câu hỏi cần một mục quy định trọn vẹn (VD Q5, có filter metadata), còn `RecursiveChunker` thắng khi thông tin cần thiết nằm rải trong nhiều đoạn văn liên tục không theo mục rõ ràng (VD Q1/Q2 về Green Tech). Bài học lớn nhất là: **không có chiến lược nào thắng tuyệt đối** — lựa chọn nên dựa vào cấu trúc thật của tài liệu (có heading rõ ràng hay không) hơn là một quy tắc chung cho mọi corpus.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ ưu tiên bật embedding thật (`OpenAIEmbedder`) và chốt đúng tên biến `.env` (`EMBEDDING_PROVIDER`, không phải `EMBEDDING_PROVIDER_ENV`) ngay từ đầu, thay vì để cả nhóm benchmark hàng chục lượt trên `_mock_embed` mà không biết mọi script đang âm thầm rơi về giả lập — đây là lỗi tốn nhiều thời gian nhất trong cả quá trình. Ngoài ra, nếu làm lại sẽ chọn thêm 1-2 tài liệu có nội dung tương tự nhau hơn (nhiều chương trình học bổng cùng nói "quy trình"/"thời hạn" bằng ngôn ngữ gần giống nhau) để bài test filter theo `category`/`audience` rõ ràng hơn, thay vì để corpus quá đa dạng chủ đề khiến một số câu hỏi (như Q3 "quy trình") khó phân biệt do tài liệu đúng quá ngắn và ít từ khoá trùng với câu hỏi.

---

## Tự Đánh Giá (Phần Nhóm)

> Điểm dưới đây là tự đánh giá tạm thời của R3 dựa trên phần đã hoàn thành (lựa chọn tài liệu, baseline, chiến lược HeadingChunker/hierarchical, benchmark, GUI demo); cần R1/R2/Report Lead xác nhận lại trước khi nộp vì bảng "So sánh giữa các thành viên" và một số insight demo vẫn còn dòng để trống chờ điền.

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 9 / 10 |
| Thiết kế chiến lược (Strategy Design) | 13 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 8 / 10 |
| Thuyết trình (Demo) | 4 / 5 |
| **Tổng phần nhóm** | **34 / 40** |
