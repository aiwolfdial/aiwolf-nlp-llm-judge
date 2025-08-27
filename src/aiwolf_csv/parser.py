from aiwolf_nlp_common.packet import Request

class AIWolfCSVParser:
    def get_action(self, line: list[str]) -> str:
        """どの行動を意味する行なのか取得."""
        return self._get_element(line, index=1)

    def get_text(self, line: list[str]) -> str:
        """エージェントの会話内容を取得する."""
        if not self._is_conversation_action(line):
            msg = "Not a conversation action"
            raise ValueError(msg)

        return self._get_element(line=line, index=5)

    def _is_conversation_action(self, line: list[str]) -> bool:
        return self.get_action(line) in (
            Request.TALK.value.lower(),
            Request.WHISPER.value.lower(),
        )

    def _get_element(self, line: list[str], index: int) -> str:
        if type(line) is not list or any([type(elem) is not str for elem in line]):
            msg = "Line must be a list of strings"
            raise TypeError(msg)
        
        if len(line) == 0 or all(elem.strip() == "" for elem in line):
            msg = "Empty line not allowed"
            raise ValueError(msg)

        if index >= len(line):
            msg = f"Index {index} out of range for line with {len(line)} elements"
            raise ValueError(msg)

        return line[index]
