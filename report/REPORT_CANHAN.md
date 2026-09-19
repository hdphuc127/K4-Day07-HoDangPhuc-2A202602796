# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Hồ Đăng Phúc
**Nhóm:** Nhóm học bổng USTH (R3 · Strategy)
**Ngày:** 19/09/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
>   Độ tương đồng cao giữa hai vector thì 2 vector đó có hướng gần nhau trong không gian vector và hai văn bản gốc có nội dung hoặc ý nghĩa tương tự.

**Ví dụ có độ tương tự CAO:**
- Câu A: Tôi thích chơi Yasuo trong Liên Minh Huyền Thoại.
- Câu B: Yasuo là tướng yêu thích của tôi trong game Liên Minh Huyền Thoại.
- Tại sao tương đồng: vì đều mang ý nghĩa là thích chơi tướng Yasuo trong game Liên Minh Huyền Thoại.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Tôi thích chơi Yasuo trong Liên Minh Huyền Thoại.
- Câu B: Tôi thích ăn phở vào buổi sáng.
- Tại sao khác: vì nội dung của hai câu hoàn toàn khác nhau, một câu nói về trò chơi điện tử và câu còn lại nói về sở thích ăn uống.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Vì cùng một ý nhưng có thể được biểu diễn bởi nhiều cách với độ dài khác nhau, cosine similarity chỉ quan tâm đến hướng của vector, không quan tâm đến độ dài vector vậy nên phù hợp cho text embeddings. Trong khi đó, Euclidean distance lại bị ảnh hưởng bởi độ dài vector, nên không phản ánh đúng mức độ tương đồng về ý nghĩa giữa các văn bản.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* Bước trượt (step) = chunk_size − overlap = 500 − 50 = 450. Số chunk = ceil((10000 − 500) / 450) + 1 = ceil(9500 / 450) + 1 = ceil(21.11) + 1 = 22 + 1 = 23.
> *Đáp án:* **23 chunks.**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Step giảm còn 400, số chunk = ceil(9500/400) + 1 = 24 + 1 = 25 chunks — tăng lên so với 23. Overlap lớn hơn giúp giảm rủi ro một câu/ý quan trọng bị cắt đúng ranh giới chunk, giữ được ngữ cảnh liền mạch hơn cho việc truy xuất, đổi lại là nhiều chunk hơn và tốn thêm chi phí embedding/lưu trữ.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng regex `(?<=[.!?])\s+|(?<=\.)\n` để tách câu: lookbehind giữ lại dấu câu ở cuối chunk trước thay vì nuốt mất, và nhánh thứ hai xử lý riêng trường hợp câu kết bằng dấu chấm rồi xuống dòng (phổ biến trong văn bản quy định dạng liệt kê). Sau khi tách, loại bỏ chuỗi rỗng/khoảng trắng thừa rồi gom mỗi `max_sentences_per_chunk` câu thành một chunk; edge case xử lý là text rỗng (trả về `[]`) và trường hợp không câu nào khớp regex (coi cả đoạn là một "câu").

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán thử lần lượt các separator theo độ ưu tiên (`\n\n`, `\n`, `. `, ` `, `""`): nếu tách bằng separator hiện tại cho ra nhiều hơn 1 phần thì dùng, phần nào vẫn dài hơn `chunk_size` sẽ được đệ quy tách tiếp bằng separator kế tiếp; nếu tách không giúp ích (≤1 phần) thì rơi xuống separator tiếp theo. Sau khi tách, các mảnh nhỏ được gộp lại (merge) cho tới sát `chunk_size` để tránh chunk quá vụn. Base case gồm hai trường hợp: `current_text` đã đủ ngắn (`len <= chunk_size`) thì trả về nguyên văn bản, và hết separator (`remaining_separators` rỗng hoặc gặp `""`) thì cắt cứng theo `chunk_size`.

**`HeadingChunker.chunk`** — hướng tiếp cận (chiến lược cá nhân, vai R3):
> Vì tài liệu học bổng của USTH đã được tác giả chia sẵn theo mục (`## I. Thông Tin Chung...`, `## II. Đối Tượng...`), tôi tách văn bản tại từng dòng heading (regex `^#{2,3}\s+.+$`) để mỗi section trở thành một chunk trọn vẹn về ngữ nghĩa, thay vì cắt cứng theo độ dài. Nếu tài liệu có ít hơn 2 heading (không đủ cấu trúc), hàm rơi về `RecursiveChunker` làm phương án dự phòng. Section nào dài hơn `chunk_size` được hạ xuống `RecursiveChunker` để chia nhỏ tiếp, và dòng heading được lặp lại ở đầu mỗi mảnh con để không mảnh nào mất ngữ cảnh "đang ở mục nào".

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> `add_documents` chuyển mỗi `Document` thành một record `{id, content, metadata, embedding}` (embedding tính qua `embedding_fn`, mặc định `_mock_embed`) rồi append vào danh sách `self._store` trong bộ nhớ — không dùng ChromaDB thật vì scope bài lab chỉ cần in-memory và giữ 42 test đơn giản. `search` embed câu query rồi tính điểm bằng tích vô hướng (`_dot`, tương đương cosine vì embedding mock đã chuẩn hoá độ dài), sắp xếp giảm dần theo score và cắt lấy `top_k`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` lọc metadata **trước** (giữ lại record nào có `record["metadata"][k] == v` cho mọi cặp trong `metadata_filter`) rồi mới chạy similarity search trên tập ứng viên đã lọc — cách này đúng vì lọc trước giúp tránh so điểm với những chunk chắc chắn không liên quan (ví dụ khác `audience`). `delete_document` xoá bằng cách giữ lại các record có `metadata["doc_id"] != doc_id`, gán lại `self._store`, và trả về `True/False` tuỳ độ dài danh sách có đổi hay không.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Prompt được dựng theo mẫu RAG: một chỉ dẫn ràng buộc agent "chỉ dùng ngữ cảnh, phải trích dẫn số nguồn, nếu thiếu thông tin phải nói rõ", theo sau là khối ngữ cảnh và câu hỏi. Ngữ cảnh được đưa vào bằng cách đánh số từng chunk top-k lấy từ `store.search`, mỗi dòng gắn `[i] (nguồn: doc_id) nội dung` để agent có thể trích dẫn nguồn cụ thể khi trả lời, tránh trả lời chung chung không kiểm chứng được.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
================================================= test session starts =================================================
platform win32 -- Python 3.13.9, pytest-9.1.1, pluggy-1.6.0 -- D:\Learning\AI_in_Action\K4-L3A-Day07-HoDangPhuc-2A202602796\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\Learning\AI_in_Action\K4-L3A-Day07-HoDangPhuc-2A202602796
plugins: anyio-4.15.1
collected 42 items                                                                                                     

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED                            [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                                     [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                              [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                               [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                                    [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED                    [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED                          [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED                           [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED                         [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                                           [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED                           [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                                      [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                                  [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                                            [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED                   [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED                       [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED                 [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED                       [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                                           [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                             [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                               [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                                     [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED                          [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED                            [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED                [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                             [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                                      [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                                     [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                                [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                            [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED                       [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED                           [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                                 [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED                           [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED        [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED                      [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED                     [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED         [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED                    [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED             [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED   [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED       [100%]

================================================= 42 passed in 0.19s ==================================================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Sinh viên cần nộp CV để xin học bổng. | Hồ sơ xin học bổng yêu cầu có sơ yếu lý lịch. | cao | -0.0382 | Sai |
| 2 | Học bổng Vallet trị giá 34 triệu đồng một suất. | Giá trị học bổng Vallet là 34.000.000 đồng. | cao | 0.0994 | Sai (điểm dương nhưng quá thấp so với mức "cao" kỳ vọng) |
| 3 | Học bổng Vallet trị giá 34 triệu đồng một suất. | Hôm nay trời Hà Nội mưa to. | thấp | 0.0923 | Sai (điểm gần như ngang với cặp 2 dù nội dung hoàn toàn khác) |
| 4 | Hạn nộp hồ sơ học bổng là ngày 21 tháng 5. | Deadline to submit the scholarship application is May 21st. | cao | -0.0358 | Sai |
| 5 | Sinh viên quốc tế được xét học bổng riêng. | Sinh viên năm nhất phải đăng ký môn học trước kỳ. | thấp | -0.0282 | Đúng (nhưng chỉ đúng "ăn may" vì điểm gần 0 giống hệt các cặp khác) |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là cặp 2 (cùng nói về giá trị học bổng Vallet, chỉ khác cách viết số) và cặp 3 (hai câu hoàn toàn không liên quan) lại cho điểm gần như nhau (~0.09-0.10), trong khi cặp 4 — cùng một câu dịch Việt-Anh — lại ra điểm âm. Điều này cho thấy `_mock_embed` (embedding giả lập dùng để test) chỉ băm ký tự/từ thành vector giả ngẫu nhiên chứ không mã hoá ý nghĩa thật, nên độ tương tự cosine tính trên nó gần như nhiễu ngẫu nhiên quanh 0 bất kể hai câu có đồng nghĩa hay không — minh chứng rằng chất lượng retrieval phụ thuộc hoàn toàn vào embedding model thật (OpenAI/local), không phải vào công thức cosine similarity.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

Chạy trên `ChromaEmbeddingStore` (ChromaDB thật, persist tại `./chroma_data/r3_real`) + `HeadingChunker(chunk_size=500, overlap=50)` (chiến lược cá nhân của R3), embedding dùng `OpenAIEmbedder` (`text-embedding-3-small`, API key thật khai báo trong `.env`).

> **Lưu ý sửa lỗi:** ban đầu `.env` khai sai tên biến (`EMBEDDING_PROVIDER_ENV=openai` thay vì `EMBEDDING_PROVIDER=openai`), khiến `resolve_embedder()` không nhận ra provider và mọi script đều âm thầm rơi về `_mock_embed`. Sau khi đổi đúng tên biến, `OpenAIEmbedder`/`ChromaEmbeddingStore` chạy được ngay vì đã có sẵn implementation trong `src/embeddings.py` và `src/chroma_store.py`.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Học bổng Green Tech 2026 có bao nhiêu suất, giá trị bao nhiêu và kéo dài bao lâu? | `usth-vallet-scholarship-2026`: mục "I. Thông Tin Chung" — cùng chủ đề học bổng nhưng sai chương trình | 0.5246 | Không (top-3 không có `usth-green-tech-scholarship-2026`) | Không nêu đúng số suất/giá trị Green Tech |
| 2 | Hạn cuối nộp hồ sơ Green Tech 2026 là ngày nào và bắt đầu khi nào? | `usth-vallet-scholarship-2026`: mục "IV. Quy Trình Phối Hợp Và Thời Hạn Nộp Hồ Sơ" | 0.5230 | Một phần (đúng chủ đề "thời hạn" nhưng sai chương trình Green Tech) | Không có mốc 23/03/2026 hay 04/2026 |
| 3 | Quy trình xét học bổng và hỗ trợ tài chính của USTH gồm những bước nào? | `usth-current-student-scholarship-2025-2026`: mục Liên hệ | 0.5401 | Có (top-3 chứa `usth-scholarship-procedure` với "Step 1") | Trích được "Step 1" nhưng thiếu Step 2/3 |
| 4 | USTH dự kiến dành bao nhiêu tiền cho quỹ học bổng 2026-2027 và áp dụng cho nhóm nào? | `usth-scholarship-application-2026`: đúng tài liệu chứa "VND 16 billion" | 0.5888 | **Có** — khớp đủ 2 gold marker | Trả lời đúng số tiền và đối tượng undergraduate |
| 5 | Đối tượng sinh viên nào được áp dụng quy định học bổng 2026 (lọc `audience: student`)? | `usth-vallet-scholarship-2026`: mục "IV. Quy Trình..." | 0.5922 | **Có** — top-3 chứa `usth-scholarship-regulation-2026` khớp đủ "Vietnamese students"/"international students" | Trả lời đúng cả hai nhóm đối tượng |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 3 / 5 (Q1 sai hoàn toàn, Q2 chỉ đúng chủ đề chứ không đúng chương trình)

### Thử nghiệm mở rộng: Hierarchical chunking (RAPTOR-style roll-up)

`src/hierarchical.py` (đã có sẵn implementation, không thuộc phạm vi chấm điểm bắt buộc của vai R3 — vai R3 chỉ yêu cầu `HeadingChunker` phẳng) cung cấp `MultiLevelChunker`: lấy chunk gốc từ một base chunker bất kỳ (ở đây dùng lại `HeadingChunker`), rồi dùng LLM thật (`OpenAISummarizer`, model `gpt-4.1-nano`) tóm tắt mỗi nhóm 5 chunk gốc thành 1 "chunk cha" ở tầng 2. Retrieval theo kiểu drill-down: tìm tầng tóm tắt trước, sau đó chỉ tìm chi tiết trong đúng nhóm chunk gốc mà bản tóm tắt trúng đó đại diện.

Để không ảnh hưởng tới dữ liệu Chroma đã dùng ở bảng trên, thử nghiệm này ghi vào **một Chroma persist directory riêng** (`./chroma_data/hierarchical_r3`, 2 collection `hier_level1`/`hier_level2`), tách biệt hoàn toàn với `./chroma_data/r3_real` (HeadingChunker phẳng) và `./chroma_data` mặc định của nhóm. Script: `benchmark/bench_hierarchical.py`.

| # | Câu hỏi | Top-1 (drill-down) | Score | Gold marker trong top-3? |
|---|---------|--------------------|-------|---------------------------|
| 1 | Số suất & giá trị Green Tech | `usth-vallet-scholarship-2026` (hạng 1), nhưng `usth-green-tech-scholarship-2026` vẫn lọt top-2 | 0.5478 | **Có** (khớp đủ 2/2) |
| 2 | Mốc thời gian Green Tech | `usth-green-tech-scholarship-2026` — đúng mục "Important Dates and Application" | 0.5080 | **Có** (khớp đủ 2/2) |
| 3 | Quy trình xét học bổng | `usth-financial-aid-2024-2025` (lễ trao học bổng) — sai hoàn toàn | 0.5546 | Không |
| 4 | Quỹ học bổng 2026-2027 | `usth-scholarship-application-2026` — đúng tài liệu | 0.6510 | **Có** (khớp đủ 2/2) |
| 5 | Đối tượng quy định 2026 (filter `audience: student`) | `usth-scholarship-regulation-2026` — đúng tài liệu | 0.6276 | **Có** (khớp đủ 2/2) |

**Kết quả: 4/5** — tốt hơn hẳn HeadingChunker phẳng (3/5) và ngang bằng RecursiveChunker của nhóm (4/5). Cụ thể Q2 (Green Tech — mốc thời gian) chuyển từ "sai chương trình" (bản phẳng) sang đúng hẳn `usth-green-tech-scholarship-2026`, vì bản tóm tắt tầng 2 gộp cả đoạn "Scholarship Value" và "Important Dates" của Green Tech lại gần nhau về mặt embedding, giúp bước drill-down khoanh đúng vùng chunk gốc cần tìm thay vì để toàn corpus cạnh tranh trực tiếp. Q3 (quy trình) vẫn sai ở cả 3 chiến lược — cho thấy hạn chế nằm ở nội dung/embedding của `usth-scholarship-procedure` chứ không phải kỹ thuật chunk. Đánh đổi: roll-up tốn thêm ~15 lệnh gọi LLM tóm tắt cho 58 chunk gốc (8 tài liệu), và độ trễ/khấu hao chi phí đó chỉ hợp lý với corpus đủ lớn để cần tầng tóm tắt trung gian — với 8 tài liệu ngắn như ở đây, lợi ích (3→4/5) có nhưng không vượt trội so với chi phí bỏ ra.

#### Điều tra sâu hơn: tại sao Q3 (quy trình) vẫn trượt, và đây có phải lỗi code không?

Đào sâu bằng cách truy vấn trực tiếp Chroma (`store_l2._collection.query(...)`, lấy `distances` thô), phát hiện: bản tóm tắt tầng 2 của đúng tài liệu (`usth-scholarship-procedure`) xếp hạng **9/15** cho câu hỏi này — thấp hơn cả các tài liệu sai chủ đề như `usth-financial-aid-2024-2025`. Trong khi đó `drill_down()` ban đầu chỉ lấy **top_k=3** summary ở tầng tóm tắt trước khi hạ xuống tầng chi tiết, nên tài liệu đúng bị loại ngay từ vòng lọc thô — dù chunk gốc của nó (chứa nguyên văn "Step 1: widely publish...") thừa sức match tốt nếu được xét tới.

**Nguyên nhân gốc:** `usth-scholarship-procedure` là tài liệu ngắn nhất corpus (1170 ký tự, thuần tiếng Anh, ít từ khoá trùng câu hỏi tiếng Việt "học bổng"/"sinh viên"), trong khi các tài liệu khác có nhiều đoạn văn tường thuật lặp "học bổng"/"sinh viên"/"hỗ trợ tài chính" nên vô tình ăn điểm cosine cao hơn ở tầng tóm tắt dù không đúng nội dung. Đây **một phần là do tham số trong code** (`top_k` dùng chung cho cả 2 tầng khiến beam ở tầng tóm tắt quá hẹp so với quy mô corpus), một phần do đặc điểm nội dung tài liệu (ngắn, ít từ khoá chung ngôn ngữ với câu hỏi).

**Thử sửa bằng cách tách 2 tham số** (`summary_beam=9` rộng hơn ở tầng tóm tắt, `top_k=3` chỉ áp cho kết quả cuối) và chạy lại toàn bộ 5 câu để đo tác động thật, không giả định:

| Beam ở tầng tóm tắt | Kết quả | Q1 (Green Tech số suất) | Q2 (Green Tech mốc thời gian) | Q3 (quy trình) |
|---|---|---|---|---|
| `summary_beam=3` (mặc định ban đầu) | **4/5** | Có | Có | Không |
| `summary_beam=9` (nới rộng để cứu Q3) | **3/5** | Không | Không | Một phần (khớp "Step 1") |

Nới beam **cứu được Q3** (chunk "Step 1" lọt vào top-3 cuối) nhưng lại **làm hỏng Q1 và Q2** — vì khi beam rộng hơn, tập ứng viên ở tầng chi tiết phình to gần bằng toàn corpus (từ ~15-20 chunk lên ~50/58 chunk), khiến bước rerank cuối cùng gần như quay lại hành vi của một tìm kiếm phẳng trên toàn corpus (vốn đã biết là trượt Q1/Q2 ở bản HeadingChunker phẳng) — lợi ích "khoanh vùng chủ đề" của hierarchical bị triệt tiêu. Do đó mình **giữ nguyên `summary_beam=3`** (mặc định) trong `benchmark/bench_hierarchical.py::drill_down()` vì thắng nhiều hơn thua trên corpus này (4/5 > 3/5), và ghi lại phát hiện này thay vì âm thầm chọn cấu hình tốt hơn cho báo cáo — đây là một đánh đổi thật giữa recall (nới beam) và precision (giữ beam hẹp), không có cấu hình nào thắng tuyệt đối ở quy mô 8 tài liệu.

> **Lưu ý sửa lỗi khác:** trong lúc chạy lại thí nghiệm này, `src/hierarchical.py` bị lỗi `NameError: name 'GEMINI_CHAT_MODEL' is not defined` (hằng số này đã bị xoá khỏi file trong khi `GeminiSummarizer` vẫn tham chiếu tới nó, khiến cả module không import được — chặn luôn cả `OpenAISummarizer` dù không liên quan tới Gemini). Đã thêm lại hằng số `GEMINI_CHAT_MODEL = "gemini-2.0-flash"` để module import được bình thường.

### GUI demo

Đã đóng gói toàn bộ 4 chiến lược chunking phẳng + kỹ thuật hierarchical roll-up + bảng kết quả benchmark thật ở trên thành một trang demo trực quan: [`chunking_demo.html`](../chunking_demo.html) (mở trực tiếp bằng trình duyệt, không cần server/API key cho phần chunking — xem thêm ở `REPORT_NHOM.md` mục 4).

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Sau khi đối chiếu kết quả benchmark thật của cả 2 đồng đội (`ket_qua_benchmark_R1.txt`, `ket_qua_benchmark_R2.txt`) với 2 cấu hình của mình, phát hiện thú vị nhất là: **R1 dùng `FixedSizeChunker`** — chiến lược đơn giản nhất, cắt cứng 500 ký tự không quan tâm ranh giới câu/mục — vẫn đạt **4/5**, cao hơn cả `HeadingChunker` phẳng của mình (3/5). Soi kỹ thì đây là "may mắn có cấu trúc": với tài liệu `usth-scholarship-procedure` (câu 3, "quy trình"), ranh giới cắt 500 ký tự của R1 tình cờ giữ "Step 1" và "Step 2" trong cùng một chunk, còn "Step 3" lọt gọn vào chunk kế — trong khi `HeadingChunker` của mình tách theo mục nhưng mục đó không được chia lại theo từng Step nên cũng chỉ khớp được 1/3. Đồng đội R2 dùng `RecursiveChunker` + embedding **local đa ngôn ngữ** (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`) lại là người duy nhất khớp đủ cả 3 "Step" cho câu này một cách vững chắc (ngay ở top-1+top-2), cho thấy với câu hỏi tiếng Việt tra cứu tài liệu tiếng Anh, một embedding model được huấn luyện đa ngôn ngữ đôi khi hiểu ý câu hỏi tốt hơn cả `text-embedding-3-small` của OpenAI mà mình đang dùng. Bài học: đừng chỉ so sánh chiến lược chunk trong nội bộ một loại embedding — phải đối chiếu chéo giữa các thành viên dùng embedding khác nhau mới thấy được đâu là giới hạn thật của chiến lược, đâu là giới hạn của mô hình embedding.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 9 / 10 |
| **Tổng phần cá nhân** | **59 / 60** |
