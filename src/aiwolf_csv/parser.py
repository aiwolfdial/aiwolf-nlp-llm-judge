from aiwolf_nlp_common.packet import Request


class AIWolfCSVParser:
    """AIWolf CSVファイルのパースを行うクラス."""

    def get_action(self, line: list[str]) -> str:
        """どの行動を意味する行なのか取得.
        
        Args:
            line: CSV行のデータ（文字列のリスト）
            
        Returns:
            行動名（文字列）
            
        Raises:
            TypeError: lineがリストでないか、要素が文字列でない場合
            ValueError: lineが空の場合
        """
        return self._get_element(line, index=1)

    def get_day(self, line: list[str]) -> int:
        """日数を取得.
        
        Args:
            line: CSV行のデータ（文字列のリスト）
            
        Returns:
            日数（整数）
            
        Raises:
            TypeError: lineがリストでないか、要素が文字列でない場合
            ValueError: lineが空の場合、または日数が整数に変換できない場合
        """
        day_str = self._get_element(line=line, index=0)
        try:
            return int(day_str)
        except ValueError as e:
            msg = f"Day must be a valid integer, got '{day_str}'"
            raise ValueError(msg) from e

    def get_text(self, line: list[str]) -> str:
        """エージェントの会話内容を取得.
        
        Args:
            line: CSV行のデータ（文字列のリスト）
            
        Returns:
            会話内容（文字列）
            
        Raises:
            TypeError: lineがリストでないか、要素が文字列でない場合
            ValueError: 会話行動でない場合、またはlineが空の場合
        """
        if not self._is_conversation_action(line):
            action = self.get_action(line)
            msg = f"Not a conversation action. Got action: '{action}'"
            raise ValueError(msg)

        return self._get_element(line=line, index=5)

    def get_speaker_index(self, line: list[str]) -> str:
        """発話者のインデックスを取得.
        
        Args:
            line: CSV行のデータ（文字列のリスト）
            
        Returns:
            発話者インデックス（文字列）
            
        Raises:
            TypeError: lineがリストでないか、要素が文字列でない場合
            ValueError: 会話行動でない場合、またはlineが空の場合
        """
        if not self._is_conversation_action(line):
            action = self.get_action(line)
            msg = f"Not a conversation action. Got action: '{action}'"
            raise ValueError(msg)

        return self._get_element(line=line, index=4)

    def _is_conversation_action(self, line: list[str]) -> bool:
        """会話行動かどうかを判定.
        
        Args:
            line: CSV行のデータ（文字列のリスト）
            
        Returns:
            会話行動の場合True、そうでなければFalse
        """
        try:
            action = self.get_action(line)
            return action in (
                Request.TALK.value.lower(),
                Request.WHISPER.value.lower(),
            )
        except (TypeError, ValueError):
            return False

    def _get_element(self, line: list[str], index: int) -> str:
        """指定されたインデックスの要素を取得.
        
        Args:
            line: CSV行のデータ（文字列のリスト）
            index: 取得したい要素のインデックス
            
        Returns:
            指定されたインデックスの要素（文字列）
            
        Raises:
            TypeError: lineがリストでないか、要素が文字列でない場合
            ValueError: lineが空の場合、またはindexが範囲外の場合
        """
        if not isinstance(line, list):
            msg = f"Line must be a list, got {type(line).__name__}"
            raise TypeError(msg)
        
        if not all(isinstance(elem, str) for elem in line):
            invalid_types = [type(elem).__name__ for elem in line if not isinstance(elem, str)]
            msg = f"All elements in line must be strings, found: {', '.join(set(invalid_types))}"
            raise TypeError(msg)

        if len(line) == 0:
            msg = "Line cannot be empty"
            raise ValueError(msg)

        if index < 0:
            msg = f"Index must be non-negative, got {index}"
            raise ValueError(msg)
            
        if index >= len(line):
            msg = f"Index {index} is out of range for line with {len(line)} elements"
            raise ValueError(msg)

        return line[index]
