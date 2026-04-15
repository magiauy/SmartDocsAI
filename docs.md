TÀI LIỆU KIẾN TRÚC & TRIỂN KHAI ỨNG DỤNG RAG PDF (TƯƠNG TỰ NOTEBOOKLM)Tài liệu này mô tả chi tiết kiến trúc, công nghệ và luồng xử lý để xây dựng một ứng dụng cho phép người dùng tải lên file PDF và đặt câu hỏi dựa trên nội dung của file đó.1. Tổng quan Công nghệ (Tech Stack)Hệ thống được thiết kế theo hướng Microservices/API-driven, tối giản và dễ dàng triển khai (Self-hosted).Trích xuất văn bản (OCR): PaddleOCR (Hoạt động như một API độc lập).Chia nhỏ văn bản (Chunking): Xử lý tại Backend (VD: dùng LangChain Text Splitter).Embedding Model: BAAI/bge-m3 (Mô hình đa ngôn ngữ, hỗ trợ tiếng Việt xuất sắc).Vector Database: Qdrant (Triển khai nội bộ qua Docker Compose).Local LLM: Qwen 1.5B / Qwen2 1.5B (Chạy qua Ollama, triển khai nội bộ qua Docker Compose).Quản lý Session Chat: In-Memory Storage (Lưu trực tiếp trên RAM của Backend).2. Cấu hình Triển khai Hạ tầng (Docker Compose)Phần lõi lưu trữ (Qdrant) và xử lý ngôn ngữ tự nhiên (Ollama/Qwen) sẽ được đóng gói chung trong một mạng lưới Docker nội bộ.version: '3.8'

services:
  # 1. Vector Database
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant_db
    ports:
      - "6333:6333" # REST API Port
    volumes:
      - ./qdrant_storage:/qdrant/storage
    restart: unless-stopped

  # 2. Local LLM Server (Ollama)
  ollama:
    image: ollama/ollama:latest
    container_name: ollama_llm
    ports:
      - "11434:11434" # Ollama API Port
    volumes:
      - ./ollama_storage:/root/.ollama
    restart: unless-stopped
Lưu ý: Sau khi chạy docker-compose up -d, cần pull model Qwen bằng lệnh: docker exec -it ollama_llm ollama run qwen2:1.5b3. Chi tiết Luồng Thực thi (Workflow)Bước 1: Trích xuất và Xử lý văn bản (Chunking)Mục đích: Lấy chữ từ file PDF (dạng ảnh scan) và chia nhỏ để model dễ hiểu.Gọi API OCR: Backend nhận file PDF từ người dùng, gửi đến API PaddleOCR.Nhận Raw Text: API PaddleOCR trả về tọa độ và các khối chữ. Backend ghép chúng lại thành một chuỗi văn bản hoàn chỉnh.Chunking: Đưa chuỗi văn bản qua thuật toán cắt đoạn (VD: RecursiveCharacterTextSplitter).Chunk size: 500 - 800 ký tự / đoạn.Chunk overlap: 100 - 150 ký tự (Giữ lại phần giao nhau để không mất ngữ nghĩa giữa hai đoạn liên tiếp).Bước 2: Embedding và Lưu trữ vào Vector DatabaseMục đích: Số hóa văn bản thành tọa độ không gian để tìm kiếm tương đồng.Tạo Vector: Backend đẩy từng chunk qua model BAAI/bge-m3 để nhận lại các vector toán học.Lưu vào Qdrant: Ghi dữ liệu vào Qdrant DB. Mỗi bản ghi (point) bắt buộc phải có:id: UUID tự sinh.vector: Dữ liệu toán học từ model BGE-M3.payload (Metadata):text: Nội dung chữ gốc của chunk.file_id: Mã định danh duy nhất của file PDF (Bắt buộc để phân biệt các file).Bước 3: Luồng RAG (Truy xuất dữ liệu)Mục đích: Tìm đúng đoạn văn bản chứa câu trả lời khi người dùng đặt câu hỏi.Người dùng gửi câu hỏi và file_id của tài liệu đang mở.Backend dùng BAAI/bge-m3 chuyển câu hỏi thành "Vector câu hỏi".Tìm kiếm trên Qdrant (Similarity Search):Điều kiện lọc (Filter): file_id = ID của file hiện tại.Lấy ra Top K (VD: 3 - 5) chunks có vector gần giống với câu hỏi nhất.Bước 4: Gom dữ liệu và Gọi LLM (Ollama)Mục đích: Tổng hợp thông tin và yêu cầu Qwen 1.5B sinh ra câu trả lời tự nhiên.Thiết kế System Prompt:"Bạn là một trợ lý ảo thông minh chuyên phân tích tài liệu. Dưới đây là các đoạn thông tin được trích xuất từ tài liệu. Hãy trả lời câu hỏi CHỈ DỰA VÀO những thông tin này. Nếu không có đáp án trong tài liệu, hãy nói 'Tài liệu không đề cập đến', tuyệt đối không tự suy diễn."Gom Payload: Backend ráp nối chuỗi theo cấu trúc: [System Prompt] + [Top K Chunks Text] + [Lịch sử Chat] + [Câu hỏi mới].Gọi API Ollama:Endpoint: http://localhost:11434/api/generateBackend gửi POST request chứa Payload trên đến container Ollama.Nhận kết quả văn bản từ Qwen và trả về cho Client.Bước 5: Quản lý Session Chat (In-Memory)Mục đích: Giúp AI nhớ được các câu hỏi trước đó trong cùng một phiên làm việc.Sử dụng cấu trúc dữ liệu toàn cục trên RAM của Backend (VD: Dictionary<string, List<Message>>).Mỗi phiên chat có một session_id.Lưu trữ tối đa 5 đến 10 vòng thoại (turn) gần nhất cho mỗi session_id.Mỗi khi gọi qua Bước 4, trích xuất danh sách lịch sử này và nhét vào Prompt.Tối ưu: Khi lịch sử vượt quá số lượng tối đa, tự động xóa các tin nhắn cũ nhất (FIFO - First In First Out) để tránh quá tải RAM và giới hạn Token của LLM.