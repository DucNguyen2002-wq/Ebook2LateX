import uuid

from app.database import SessionLocal

from app.models import User, Document, FormulaEntry


def seed_data():

    # 1. Khởi tạo phiên làm việc (Session)

    db = SessionLocal()

    

    try:

        print("Đang tạo dữ liệu...")


        # 2. Tạo dữ liệu cho bảng User

        # Lưu ý: Trong thực tế mật khẩu cần được băm (hash), ở đây ta nhập mật khẩu tượng trưng

        test_user = User(

            user_id=uuid.uuid4(),

            username_email="teo@dalat.edu.vn",

            password_hash="hashed_password_here",

            full_name="Lê Văn Tèo",

            role="Admin"

        )

        db.add(test_user)

        db.flush() # Đẩy dữ liệu tạm thời để lấy user_id cho bảng sau


        # 3. Tạo dữ liệu mẫu cho bảng Documents

        test_doc = Document(

            id=uuid.uuid4(),

            user_id=test_user.user_id,

            file_name="Giao_trinh_Toan_12.pdf",

            file_path_url="/uploads/toan12.pdf",

            status="Completed"

        )

        db.add(test_doc)

        db.flush()


        # 4. Tạo dữ liệu mẫu cho bảng FormulaEntries (Công thức LaTeX)

        formula = FormulaEntry(

            id=uuid.uuid4(),

            document_id=test_doc.id,

            latex_content=r"\frac{-b \pm \sqrt{b^2 - 4ac}}{2a}",

            order_index=1

        )

        db.add(formula)


        # 5. Xác nhận lưu toàn bộ thay đổi vào Database

        db.commit()

        print("Tạo dữ liệu thành công! Kiểm tra pgAdmin4 để xem kết quả.")


    except Exception as e:

        print(f"Có lỗi xảy ra: {e}")

        db.rollback() # Hoàn tác nếu có lỗi để tránh rác dữ liệu

    finally:

        db.close() # Luôn đóng kết nối sau khi xong


if __name__ == "__main__":

    seed_data()