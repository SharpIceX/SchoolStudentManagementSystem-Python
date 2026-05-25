import sys
import logging
import sqlite3
import contextlib
from pathlib import Path
from collections.abc import Callable, Generator

"""
1. Python 内置的 Sqlite3 简直比 NodeJS 内置的还抽象难用
2. 这是新鲜的屎山
"""


# region 全局配置
class StoreContext:
	def __init__(self) -> None:
		self.data_path: Path | None = None
		self.database_path: Path | None = None
		self.log_path: Path | None = None


store = StoreContext()

# endregion


# region 数据库操作
class Database:
	@staticmethod
	@contextlib.contextmanager
	def connection() -> Generator[sqlite3.Connection]:
		path = store.database_path

		# 替代方案：显式检查并抛出异常
		if path is None:
			msg = '数据库路径未初始化'
			raise ValueError(msg)

		conn = sqlite3.connect(path)
		conn.row_factory = sqlite3.Row
		try:
			yield conn
			conn.commit()
		except Exception:
			conn.rollback()
			raise
		finally:
			conn.close()


# endregion


# region 终端颜色格式化工具
class ConsoleColor:
	"""为文本包装颜色"""

	_RED = '\033[31m'
	_GREEN = '\033[32m'
	_YELLOW = '\033[33m'
	_BLUE = '\033[34m'
	_RESET = '\033[0m'

	@classmethod
	def red(cls, text: str) -> str:
		"""包装为红色文本"""
		return f'{cls._RED}{text}{cls._RESET}'

	@classmethod
	def green(cls, text: str) -> str:
		"""包装为绿色文本"""
		return f'{cls._GREEN}{text}{cls._RESET}'

	@classmethod
	def yellow(cls, text: str) -> str:
		"""包装为黄色文本"""
		return f'{cls._YELLOW}{text}{cls._RESET}'

	@classmethod
	def blue(cls, text: str) -> str:
		"""包装为蓝色文本"""
		return f'{cls._BLUE}{text}{cls._RESET}'


# endregion


# region 按回车继续
def wait_for_enter() -> None:
	"""「按回车继续」实现"""
	print(ConsoleColor.green('\n按回车键继续...'))
	with contextlib.suppress(KeyboardInterrupt, EOFError):
		input()


# endregion


# region 高亮关键字
def highlight_keywork(text: str | None, keyword: str) -> str:
	"""自动包裹关键字为红色字体，处理空值"""
	if not keyword or text is None:
		return str(text) if text is not None else ''

	return str(text).replace(keyword, ConsoleColor.red(keyword))


# endregion


# region 格式化数据库列输出
def format_student_row(row: sqlite3.Row, *, highlight_keyword: str = '') -> str:
	"""
	将学生信息从数据库列格式化为人类友好风格
	"""
	parts = [
		f'学号: {highlight_keywork(row["student_id"], highlight_keyword)}',
		f'姓名: {highlight_keywork(row["name"], highlight_keyword)}',
		f'性别: {highlight_keywork(row["sex"], highlight_keyword)}',
		f'出生日期: {highlight_keywork(row["birth_date"], highlight_keyword)}',
		f'院系: {highlight_keywork(row["college"], highlight_keyword)}',
		f'班级: {highlight_keywork(row["class"], highlight_keyword)}',
		f'手机号: {highlight_keywork(row["phone_number"], highlight_keyword)}',
		f'状态: {highlight_keywork(row["status"], highlight_keyword)}',
		f'创建时间: {row["created_time"]}',
		f'更新时间: {row["updated_time"]}',
	]
	return ' | '.join(parts)


# endregion


# region 批量输出学生信息
def print_query_results(rows: list[sqlite3.Row], highlight: str = '') -> None:
	"""批量输出学生信息"""
	if not rows:
		print(ConsoleColor.yellow('没有查询到匹配的学生信息。'))
		return

	print(f'共查询到 {len(rows)} 条记录：')
	for row in rows:
		print(format_student_row(row, highlight_keyword=highlight))


# endregion


# region 日志系统
class Logger:
	"""日志系统"""

	_logger = logging.getLogger('AppLogger')
	_file_handler: logging.FileHandler | None = None

	@classmethod
	def init(cls, log_file_path: Path) -> None:
		cls._logger.setLevel(logging.INFO)

		if cls._logger.hasHandlers():
			cls._logger.handlers.clear()

		cls._file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
		file_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
		cls._file_handler.setFormatter(file_formatter)
		cls._logger.addHandler(cls._file_handler)

	@classmethod
	def info(cls, message: str) -> None:
		cls._logger.info(message)

	@classmethod
	def warn(cls, message: str) -> None:
		cls._logger.warning(message)

	@classmethod
	def error(cls, message: str, *, exc_info: bool = False) -> None:
		cls._logger.error(message, exc_info=exc_info)


# endregion


# region 菜单引擎
def handle_menu(title: str, menu_map: dict[str, Callable[[], None]]) -> bool:
	"""
	自动化菜单处理器
	:param title: 菜单标题
	:param menu_map: 选项映射表
	:return: 是否退出系统 (True: 退出, False: 继续)
	"""

	options_list: list[str] = list(menu_map.keys())

	# 菜单内容
	content = f'--- 学校学生管理系统 - {title} ---\n'
	content += '\n'.join(f'{i}. {name}' for i, name in enumerate(options_list, 1))
	content += '\n0. 退出系统'
	content += '\n---------------------------------'

	while True:
		print(ConsoleColor.blue(content))
		choice = input(f'请选择操作 {ConsoleColor.blue("❯")} ').strip()

		if choice == '0':
			print(ConsoleColor.green('退出当前菜单'))
			return True

		if choice.isdigit():
			index = int(choice) - 1
			if 0 <= index < len(options_list):
				selected_name = options_list[index]
				menu_map[selected_name]()
				wait_for_enter()
				continue

		print(ConsoleColor.red('输入错误，请输入正确的选项数字！'))


# endregion


# region 「添加学生」菜单
def add_student() -> None:
	print('--- 添加学生 ---')

	# 基础信息
	student_id = input('学号: ').strip()
	name = input('名字: ').strip()
	sex = input('性别 (男/女): ').strip()
	birth_date = input('出生日期 (YYYY-MM-DD): ').strip() or None
	college = input('院系: ').strip()
	class_name = input('班级: ').strip()
	phone = input('手机号: ').strip()
	status = input('状态 (在读/休学/毕业/退学) [默认: 在读]: ').strip() or '在读'

	sql = """
INSERT INTO students (student_id, name, sex, birth_date, college, class, phone_number, status)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """

	try:
		with Database.connection() as conn:
			conn.execute(sql, (student_id, name, sex, birth_date, college, class_name, phone, status))
		print(ConsoleColor.green('学生添加成功！'))
		Logger.info(f'成功添加学生: {student_id} - {name}')
	except sqlite3.IntegrityError as e:
		error_msg = f'添加失败：学号或手机号已存在。详细错误: {e}'
		print(ConsoleColor.red(error_msg))
		Logger.error(error_msg)
	except sqlite3.Error as e:
		error_msg = f'数据库操作失败: {e}'
		print(ConsoleColor.red(error_msg))
		Logger.error('数据库操作失败', exc_info=True)


# endregion


# region 「删除学生」菜单
def delete_student() -> None:
	print('--- 删除学生 ---')
	student_id = input('请输入要删除的学号: ').strip()

	# 查找学生信息
	with Database.connection() as conn:
		cursor = conn.execute('SELECT * FROM students WHERE student_id = ?', (student_id,))
		student = cursor.fetchone()

	if not student:
		print(ConsoleColor.red(f'未找到学号为 {student_id} 的学生。'))
		return

	# 二次确认
	confirm = input(f'确定要删除学生【{student["name"]}】吗？(y/n): ').strip().lower()
	if confirm != 'y':
		print(ConsoleColor.yellow('已取消删除操作。'))
		return

	# 日志事务
	student_data = dict(student)
	Logger.info(f'执行删除操作，被删除学生数据备份: {student_data}')

	# 删除事务
	try:
		with Database.connection() as conn:
			conn.execute('DELETE FROM students WHERE student_id = ?', (student_id,))
		print(ConsoleColor.green(f'学生 {student_id} 已成功删除。'))
	except sqlite3.Error as e:
		error_msg = f'删除失败: {e}'
		print(ConsoleColor.red(error_msg))
		Logger.error(error_msg, exc_info=True)


# endregion


# region 「更新学生信息」菜单
def update_student() -> None:
	print('--- 更新学生信息 ---')
	student_id = input('请输入要更新的学生学号: ').strip()

	with Database.connection() as conn:
		cursor = conn.execute('SELECT * FROM students WHERE student_id = ?', (student_id,))
		student_row = cursor.fetchone()

	if not student_row:
		print(ConsoleColor.red(f'未找到学号为 {student_id} 的学生。'))
		return

	fields: dict[str, str] = {
		'name': '名字',
		'sex': '性别 (男/女)',
		'birth_date': '出生日期 (YYYY-MM-DD)',
		'college': '院系',
		'class': '班级',
		'phone_number': '手机号',
		'status': '状态 (在读/休学/毕业/退学)',
	}

	updates: dict[str, str] = {}
	print(f'正在更新学生: {student_row["name"]} (直接回车保持原值)')

	for field, label in fields.items():
		current_val = str(student_row[field])
		new_val = input(f'{label} [{current_val}]: ').strip()
		if new_val:
			updates[field] = new_val

	if not updates:
		print(ConsoleColor.yellow('没有输入任何更新内容。'))
		return

	set_clause = ', '.join([f'{k} = ?' for k in updates])
	values = list(updates.values())
	values.append(student_id)

	# ! 这里有 SQL 注入分享，但是非生产项目懒得处理了
	sql = f'UPDATE students SET {set_clause} WHERE student_id = ?'  # noqa: S608

	try:
		with Database.connection() as conn:
			conn.execute(sql, tuple(values))
		print(ConsoleColor.green(f'学生 {student_id} 信息更新成功！'))
		Logger.info(f'成功更新学生: {student_id}，字段: {list(updates.keys())}')
	except sqlite3.IntegrityError as e:
		error_msg = f'更新失败：学号或手机号冲突。详细错误: {e}'
		print(ConsoleColor.red(error_msg))
		Logger.error(error_msg)
	except sqlite3.Error as e:
		error_msg = f'数据库更新失败: {e}'
		print(ConsoleColor.red(error_msg))
		Logger.error(error_msg, exc_info=True)


# endregion


# region 「查询学生信息」菜单
def query_students() -> None:
	menu = {
		'列出所有学生': query_list_all_students,
		'模糊查询（全字段）': query_fuzzy_all_fields,
		'按学号查询': query_by_student_id,
		'按名字查询': query_by_name,
	}
	handle_menu('查询学生信息', menu)


# endregion


# region 「询查学生信息——列出所有学生」菜单
def query_list_all_students() -> None:
	with Database.connection() as conn:
		rows = conn.execute('SELECT * FROM students').fetchall()
		print_query_results(rows)


# endregion


# region 「询查学生信息——模糊查询」菜单
def query_fuzzy_all_fields() -> None:
	keyword = input('请输入模糊查询关键字: ').strip()
	if not keyword:
		return

	cols = ['student_id', 'name', 'sex', 'college', 'class', 'phone_number', 'status']
	query = ' OR '.join([f'{col} LIKE ?' for col in cols])
	params = [f'%{keyword}%' for _ in cols]

	with Database.connection() as conn:
		# ! 这里有 SQL 注入分享，但是非生产项目懒得处理了
		rows = conn.execute(f'SELECT * FROM students WHERE {query}', params).fetchall()  # noqa: S608
		print_query_results(rows, highlight=keyword)


# endregion


# region 「询查学生信息——按学号查询」菜单
def query_by_student_id() -> None:
	student_id = input('请输入学号: ').strip()
	with Database.connection() as conn:
		row = conn.execute('SELECT * FROM students WHERE student_id = ?', (student_id,)).fetchone()
		if row:
			print(format_student_row(row))
		else:
			print(ConsoleColor.red('未找到该学号的学生。'))


# endregion


# region 「询查学生信息——按名字查询」菜单
def query_by_name() -> None:
	name = input('请输入学生姓名: ').strip()
	with Database.connection() as conn:
		rows = conn.execute('SELECT * FROM students WHERE name LIKE ?', (f'%{name}%',)).fetchall()
		print_query_results(rows, highlight=name)


# endregion


# region 主菜单
def menu_home() -> None:
	menu_actions = {
		'添加学生': add_student,
		'删除学生': delete_student,
		'更新学生信息': update_student,
		'查询学生信息': query_students,
	}

	while True:
		if handle_menu('主菜单', menu_actions):
			break


# endregion


# region 入口点
def bootstrap() -> None:
	data_path = (Path(__file__).resolve().parent / '../data').resolve()
	log_path = (data_path / 'running.log').resolve()
	database_path = (data_path / 'data.db').resolve()

	# 初始化数据目录
	print(f'数据目录：{data_path}')
	if not data_path.exists():
		data_path.mkdir(parents=True, exist_ok=True)
	elif not data_path.is_dir():
		print(f'数据路径已存在，但不是一个目录: {data_path}')
		sys.exit(1)

	# 日志
	Logger.init(log_path)
	Logger.info('系统启动')

	# 初始化数据库
	if not database_path.exists():
		with sqlite3.connect(database_path) as conn:
			init_sql_file_path = Path(__file__).resolve().parent / 'sql/init.sql'
			sql_script = init_sql_file_path.read_text(encoding='utf-8')
			conn.executescript(sql_script)
			conn.commit()
	elif not database_path.is_file():
		print(f'数据库路径存在，但不是文件: {database_path}')
		sys.exit(1)

	# 存储到全局数据
	store.data_path = data_path
	store.log_path = log_path
	store.database_path = database_path

	try:
		menu_home()
	except KeyboardInterrupt:
		message = '发现 SIGINT 信号'
		print(ConsoleColor.yellow(f'\n\n{message}'))
		Logger.warn(message)
		logging.shutdown()
		sys.exit(130)
	except Exception as error:  # noqa: BLE001
		print(ConsoleColor.red(f'未知错误：\n{error}'))
		Logger.error(f'未知错误：\n{error}', exc_info=True)
		logging.shutdown()
		sys.exit(1)


# endregion

if __name__ == '__main__':
	bootstrap()
