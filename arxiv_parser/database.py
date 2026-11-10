"""数据库管理模块"""

import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from contextlib import contextmanager

from loguru import logger

from .models import (
    PaperMetadata, DownloadedPaper, ParsedPaper, AnalyzedPaper,
    PaperStatus, AnalysisResult, QAPair, ImageInfo, TableInfo, Reference
)


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str = "output/papers.db"):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            conn.close()
    
    def _init_database(self):
        """初始化数据库表结构"""
        schema = f"""
        -- 存储策略：
        --   字符串数组（authors/categories/innovations/keywords）以 JSON 文本存储，
        --   属于「文档型」字段，不参与关系型 join；结构化实体
        --   （sections/images/tables/references/qa_pairs）使用正规关系表。

        -- 论文元数据表
        CREATE TABLE IF NOT EXISTS papers (
            arxiv_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            authors TEXT,  -- JSON 数组
            abstract TEXT,
            full_text TEXT,  -- 全文正文
            categories TEXT,  -- JSON 数组
            primary_category TEXT,
            published_date TEXT,
            updated_date TEXT,
            pdf_url TEXT,
            entry_id TEXT,
            
            -- 文件路径
            local_pdf_path TEXT,
            image_dir TEXT,
            
            -- 处理状态
            download_status TEXT DEFAULT '{PaperStatus.PENDING.value}',
            parse_status TEXT DEFAULT '{PaperStatus.PENDING.value}',
            analyze_status TEXT DEFAULT '{PaperStatus.PENDING.value}',
            
            -- 统计信息
            file_size INTEGER,
            page_count INTEGER,
            
            -- 时间戳
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );
        
        -- LLM 分析结果表
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            arxiv_id TEXT NOT NULL,
            llm_model TEXT NOT NULL,
            
            -- 摘要
            summary_zh TEXT,
            summary_en TEXT,
            
            -- 分析内容
            innovations TEXT,  -- JSON 数组
            methodology TEXT,
            experiments TEXT,
            conclusions TEXT,
            
            -- 评分
            novelty_score INTEGER,
            quality_score INTEGER,
            
            -- 关键词
            keywords TEXT,  -- JSON 数组
            
            -- 元数据
            analysis_time TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            
            FOREIGN KEY (arxiv_id) REFERENCES papers(arxiv_id)
        );
        
        -- 问答对表
        CREATE TABLE IF NOT EXISTS qa_pairs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            qa_type TEXT,  -- 'understanding', 'application', 'comparison'
            
            FOREIGN KEY (analysis_id) REFERENCES analysis_results(id)
        );
        
        -- 图片信息表
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            arxiv_id TEXT NOT NULL,
            image_path TEXT NOT NULL,
            page_number INTEGER,
            caption TEXT,
            image_type TEXT,  -- 'figure', 'table', 'equation'
            
            FOREIGN KEY (arxiv_id) REFERENCES papers(arxiv_id)
        );
        
        -- 表格信息表
        CREATE TABLE IF NOT EXISTS tables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            arxiv_id TEXT NOT NULL,
            table_path TEXT,
            page_number INTEGER,
            caption TEXT,
            table_data TEXT,  -- JSON 格式
            
            FOREIGN KEY (arxiv_id) REFERENCES papers(arxiv_id)
        );
        
        -- 参考文献表
        CREATE TABLE IF NOT EXISTS references_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            arxiv_id TEXT NOT NULL,
            ref_id TEXT,
            ref_text TEXT,
            ref_title TEXT,
            ref_authors TEXT,
            ref_year INTEGER,
            ref_venue TEXT,
            
            FOREIGN KEY (arxiv_id) REFERENCES papers(arxiv_id)
        );
        
        -- 论文章节表
        CREATE TABLE IF NOT EXISTS sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            arxiv_id TEXT NOT NULL,
            section_title TEXT,
            section_level INTEGER,
            content TEXT,
            page_start INTEGER,
            page_end INTEGER,
            
            FOREIGN KEY (arxiv_id) REFERENCES papers(arxiv_id)
        );
        
        -- 创建索引
        CREATE INDEX IF NOT EXISTS idx_papers_categories ON papers(categories);
        CREATE INDEX IF NOT EXISTS idx_papers_primary_category ON papers(primary_category);
        CREATE INDEX IF NOT EXISTS idx_papers_published_date ON papers(published_date);
        CREATE INDEX IF NOT EXISTS idx_analysis_arxiv_id ON analysis_results(arxiv_id);
        CREATE INDEX IF NOT EXISTS idx_qa_analysis_id ON qa_pairs(analysis_id);
        CREATE INDEX IF NOT EXISTS idx_images_arxiv_id ON images(arxiv_id);
        CREATE INDEX IF NOT EXISTS idx_tables_arxiv_id ON tables(arxiv_id);
        CREATE INDEX IF NOT EXISTS idx_references_arxiv_id ON references_table(arxiv_id);
        CREATE INDEX IF NOT EXISTS idx_sections_arxiv_id ON sections(arxiv_id);
        """
        
        with self.get_connection() as conn:
            conn.executescript(schema)
            self._migrate(conn)
            logger.info(f"数据库初始化完成: {self.db_path}")

    def _migrate(self, conn):
        """处理已有数据库的列迁移"""
        existing = {row[1] for row in conn.execute("PRAGMA table_info(papers)")}
        if 'full_text' not in existing:
            conn.execute("ALTER TABLE papers ADD COLUMN full_text TEXT")
            logger.info("迁移: papers 表新增 full_text 列")
    
    # ========== 论文元数据操作 ==========
    
    def save_paper_metadata(self, metadata: PaperMetadata) -> str:
        """保存论文元数据"""
        import json
        
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO papers (
                    arxiv_id, title, authors, abstract, categories,
                    primary_category, published_date, updated_date,
                    pdf_url, entry_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metadata.arxiv_id,
                metadata.title,
                json.dumps(metadata.authors, ensure_ascii=False),
                metadata.abstract,
                json.dumps(metadata.categories, ensure_ascii=False),
                metadata.primary_category,
                metadata.published_date,
                metadata.updated_date,
                metadata.pdf_url,
                metadata.entry_id
            ))
        
        logger.debug(f"保存论文元数据: {metadata.arxiv_id}")
        return metadata.arxiv_id
    
    def get_paper_metadata(self, arxiv_id: str) -> Optional[PaperMetadata]:
        """获取论文元数据"""
        import json

        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM papers WHERE arxiv_id = ?",
                (arxiv_id,)
            ).fetchone()

            if not row:
                return None

            authors = json.loads(row['authors'] or '[]')
            
            return PaperMetadata(
                arxiv_id=row['arxiv_id'],
                title=row['title'],
                authors=authors,
                abstract=row['abstract'] or '',
                categories=json.loads(row['categories'] or '[]'),
                primary_category=row['primary_category'] or '',
                published_date=row['published_date'] or '',
                updated_date=row['updated_date'] or '',
                pdf_url=row['pdf_url'] or '',
                entry_id=row['entry_id'] or ''
            )
    
    def paper_exists(self, arxiv_id: str) -> bool:
        """检查论文是否已存在"""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM papers WHERE arxiv_id = ?",
                (arxiv_id,)
            ).fetchone()
            return row is not None

    def get_full_text(self, arxiv_id: str) -> Optional[str]:
        """获取论文全文（支持不带版本号的 ID，如 1706.03762 匹配 1706.03762v7）"""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT full_text FROM papers WHERE arxiv_id = ? OR arxiv_id LIKE ?",
                (arxiv_id, arxiv_id + 'v%')
            ).fetchone()
            return row['full_text'] if row and row['full_text'] else None

    def get_paper_status(self, arxiv_id: str) -> Dict[str, str]:
        """获取论文各阶段处理状态（供断点续处理判断）"""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT download_status, parse_status, analyze_status FROM papers WHERE arxiv_id = ?",
                (arxiv_id,)
            ).fetchone()
            if not row:
                return {}
            return {
                'download_status': row['download_status'],
                'parse_status': row['parse_status'],
                'analyze_status': row['analyze_status'],
            }

    def update_paper_status(self, arxiv_id: str, status_field: str, status: str):
        """更新论文处理状态"""
        valid_fields = ['download_status', 'parse_status', 'analyze_status']
        if status_field not in valid_fields:
            raise ValueError(f"Invalid status field: {status_field}")
        
        with self.get_connection() as conn:
            conn.execute(f"""
                UPDATE papers
                SET {status_field} = ?, updated_at = datetime('now')
                WHERE arxiv_id = ?
            """, (status, arxiv_id))

    def save_parsed_paper(self, parsed: ParsedPaper) -> None:
        """保存解析结果：全文、章节、图片、表格、参考文献"""
        import json

        downloaded = parsed.downloaded
        arxiv_id = downloaded.metadata.arxiv_id

        with self.get_connection() as conn:
            # 更新 papers 表：全文、路径、页数、文件大小、解析状态
            conn.execute(f"""
                UPDATE papers SET
                    full_text = ?,
                    local_pdf_path = ?,
                    page_count = ?,
                    file_size = ?,
                    parse_status = '{PaperStatus.COMPLETED.value}',
                    updated_at = datetime('now')
                WHERE arxiv_id = ?
            """, (
                parsed.full_text,
                downloaded.local_pdf_path,
                parsed.page_count,
                downloaded.file_size,
                arxiv_id
            ))

            # 清空旧解析数据，保证幂等
            for table in ('sections', 'images', 'tables', 'references_table'):
                conn.execute(f"DELETE FROM {table} WHERE arxiv_id = ?", (arxiv_id,))

            # 保存章节
            for section in parsed.sections:
                conn.execute("""
                    INSERT INTO sections (arxiv_id, section_title, section_level, content, page_start, page_end)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (arxiv_id, section.name, section.level, section.content, section.start_page, section.end_page))

            # 保存图片
            for img in parsed.images:
                conn.execute("""
                    INSERT INTO images (arxiv_id, image_path, page_number, caption, image_type)
                    VALUES (?, ?, ?, ?, ?)
                """, (arxiv_id, img.local_path, img.page_number, img.caption, 'figure'))

            # 保存表格
            for tbl in parsed.tables:
                conn.execute("""
                    INSERT INTO tables (arxiv_id, table_path, page_number, caption, table_data)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    arxiv_id,
                    None,
                    tbl.page_number,
                    tbl.caption,
                    json.dumps(tbl.data, ensure_ascii=False) if tbl.data else None
                ))

            # 保存参考文献
            for ref in parsed.references:
                conn.execute("""
                    INSERT INTO references_table (arxiv_id, ref_id, ref_text)
                    VALUES (?, ?, ?)
                """, (arxiv_id, ref.ref_id, ref.text))

        logger.debug(f"保存解析结果: {arxiv_id} ({len(parsed.sections)} 章节, {len(parsed.images)} 图片, {len(parsed.references)} 参考文献)")

    def search_papers(
        self,
        category: Optional[str] = None,
        author: Optional[str] = None,
        keyword: Optional[str] = None,
        limit: int = 50
    ) -> List[PaperMetadata]:
        """搜索论文"""
        import json

        query = "SELECT * FROM papers WHERE 1=1"
        params = []
        
        if category:
            query += " AND categories LIKE ?"
            params.append(f'%{category}%')
        
        if author:
            query += " AND authors LIKE ?"
            params.append(f'%{author}%')
        
        if keyword:
            query += " AND (title LIKE ? OR abstract LIKE ?)"
            params.extend([f'%{keyword}%', f'%{keyword}%'])
        
        query += " ORDER BY published_date DESC LIMIT ?"
        params.append(limit)
        
        with self.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            
            results = []
            for row in rows:
                authors = json.loads(row['authors'] or '[]')
                results.append(PaperMetadata(
                    arxiv_id=row['arxiv_id'],
                    title=row['title'],
                    authors=authors,
                    abstract=row['abstract'] or '',
                    categories=json.loads(row['categories'] or '[]'),
                    primary_category=row['primary_category'] or '',
                    published_date=row['published_date'] or '',
                    updated_date=row['updated_date'] or '',
                    pdf_url=row['pdf_url'] or '',
                    entry_id=row['entry_id'] or ''
                ))
            
            return results
    
    # ========== 分析结果操作 ==========
    
    def save_analysis_result(self, arxiv_id: str, analysis: AnalyzedPaper) -> int:
        """保存分析结果"""
        import json

        with self.get_connection() as conn:
            # 删除旧的同名分析结果及其问答对，保证幂等
            old_ids = [r[0] for r in conn.execute(
                "SELECT id FROM analysis_results WHERE arxiv_id = ?", (arxiv_id,)
            ).fetchall()]
            for old_id in old_ids:
                conn.execute("DELETE FROM qa_pairs WHERE analysis_id = ?", (old_id,))
            conn.execute("DELETE FROM analysis_results WHERE arxiv_id = ?", (arxiv_id,))

            cursor = conn.execute("""
                INSERT INTO analysis_results (
                    arxiv_id, llm_model, summary_zh, summary_en,
                    innovations, methodology, experiments, conclusions,
                    novelty_score, quality_score, keywords, analysis_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                arxiv_id,
                analysis.llm_model,
                analysis.summary_zh,
                analysis.summary_en,
                json.dumps(analysis.innovations, ensure_ascii=False),
                analysis.methodology,
                analysis.experiments,
                analysis.conclusions,
                analysis.novelty_score,
                analysis.quality_score,
                json.dumps(analysis.keywords, ensure_ascii=False),
                analysis.analysis_time
            ))
            
            analysis_id = cursor.lastrowid
            
            # 保存问答对
            for qa in analysis.qa_pairs:
                conn.execute("""
                    INSERT INTO qa_pairs (analysis_id, question, answer, qa_type)
                    VALUES (?, ?, ?, ?)
                """, (analysis_id, qa.question, qa.answer, qa.qa_type))
        
        logger.debug(f"保存分析结果: {arxiv_id} -> analysis_id={analysis_id}")
        return analysis_id
    
    def get_analysis_result(self, arxiv_id: str) -> Optional[AnalysisResult]:
        """获取最新的分析结果"""
        import json
        
        with self.get_connection() as conn:
            row = conn.execute("""
                SELECT * FROM analysis_results 
                WHERE arxiv_id = ?
                ORDER BY created_at DESC LIMIT 1
            """, (arxiv_id,)).fetchone()
            
            if not row:
                return None
            
            # 获取问答对
            qa_rows = conn.execute("""
                SELECT question, answer, qa_type FROM qa_pairs
                WHERE analysis_id = ?
            """, (row['id'],)).fetchall()
            
            qa_pairs = [
                QAPair(
                    question=qr['question'],
                    answer=qr['answer'],
                    qa_type=qr['qa_type']
                )
                for qr in qa_rows
            ]
            
            return AnalysisResult(
                arxiv_id=arxiv_id,
                llm_model=row['llm_model'],
                summary_zh=row['summary_zh'] or '',
                summary_en=row['summary_en'] or '',
                innovations=json.loads(row['innovations'] or '[]'),
                methodology=row['methodology'] or '',
                experiments=row['experiments'] or '',
                conclusions=row['conclusions'] or '',
                novelty_score=row['novelty_score'],
                quality_score=row['quality_score'],
                keywords=json.loads(row['keywords'] or '[]'),
                qa_pairs=qa_pairs,
                analysis_time=row['analysis_time']
            )
    
    # ========== 统计查询 ==========
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        with self.get_connection() as conn:
            stats = {}
            
            # 论文总数
            stats['total_papers'] = conn.execute(
                "SELECT COUNT(*) FROM papers"
            ).fetchone()[0]
            
            # 各状态数量
            for status in ['downloaded', 'parsed', 'analyzed']:
                count = conn.execute(
                    f"SELECT COUNT(*) FROM papers WHERE {status}_status = '{PaperStatus.COMPLETED.value}'"
                ).fetchone()[0]
                stats[f'{status}_count'] = count
            
            # 分类统计
            rows = conn.execute("""
                SELECT primary_category, COUNT(*) as count
                FROM papers
                GROUP BY primary_category
                ORDER BY count DESC
                LIMIT 10
            """).fetchall()
            stats['top_categories'] = {row[0]: row[1] for row in rows}
            
            return stats
