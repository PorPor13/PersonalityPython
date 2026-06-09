import sys
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QRadioButton, QButtonGroup,
    QTableWidget, QTableWidgetItem, QLineEdit, QMessageBox,
    QHeaderView, QDialog, QFormLayout, QComboBox, QGroupBox,
    QStackedWidget, QSpinBox, QScrollArea
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont

# Setup logging
logging.basicConfig(
    filename='personality_assessment.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Constants
PERSONALITY_TYPES = ["Extrovert", "Introvert", "Ambivert"]
ANSWER_OPTIONS = ["Strongly agree", " Agree", "Neutral", "Disagree", "Strongly disagree"]

# PersonalityRule class
class PersonalityRule:
    """Represents a rule for personality type prediction"""
    def __init__(self, rule_id: str, conditions: Dict[str, str], personality: str, confidence: float = 0.8):
        self.rule_id = rule_id
        self.conditions = conditions
        self.personality = personality
        self.confidence = max(0.0, min(confidence, 1.0))
        self.created_date = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'rule_id': self.rule_id,
            'conditions': self.conditions,
            'personality': self.personality,
            'confidence': self.confidence,
            'created_date': self.created_date
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PersonalityRule':
        return cls(
            data['rule_id'],
            data['conditions'],
            data['personality'],
            data.get('confidence', 0.8)
        )

# InferenceEngine
class InferenceEngine:
    """Handles personality prediction using forward chaining"""
    def __init__(self, rules: List[PersonalityRule], questions: List[Dict[str, Any]]):
        self.rules = rules
        self.questions = questions
        self.personality_descriptions = {
            "Extrovert": (
                "You are an energetic and outgoing individual who thrives on social interaction. "
                "You gain energy from being around others and enjoy collaborative, fast-paced environments. "
                "Your strengths lie in communication and leadership.",
                "Potential career paths: Sales Manager, Public Relations Specialist, Event Planner."
            ),
            "Introvert": (
                "You are a thoughtful and reserved individual who enjoys spending time alone or in small groups. "
                "You prefer a calm environment for deep focus and introspection. Your strengths are in observation, analysis, and independent work.",
                "Potential career paths: Data Analyst, Writer, Software Developer."
            ),
            "Ambivert": (
                "You have a balanced personality, displaying traits of both introversion and extroversion. "
                "You can adapt well to various social situations and are comfortable working alone or with a team. "
                "You are versatile and can thrive in many roles.",
                "Potential career paths: Project Manager, Teacher, Human Resources Manager."
            )
        }

    def diagnose(self, answers: Dict[str, str]) -> List[tuple[str, float, str, str]]:
        if not answers:
            logging.warning("No answers provided for diagnosis")
            return []
        results = []
        answer_weights = {
            "Strongly agree": 1.0, " Agree": 0.75, "Neutral": 0.5,
            "Disagree": 0.25, "Strongly disagree": 0.0
        }
        for rule in self.rules:
            score = 0.0
            total_weight = 0.0
            for qid, answer in rule.conditions.items():
                question = next((q for q in self.questions if q['id'] == qid), None)
                if question and qid in answers and answers[qid] == answer:
                    score += question.get('weight', 1.0) * answer_weights.get(answers[qid], 0.5)
                    total_weight += question.get('weight', 1.0)
            if total_weight > 0:
                match_ratio = score / total_weight
                adjusted_confidence = rule.confidence * match_ratio
                if match_ratio >= 0.4:
                    description, jobs = self.personality_descriptions[rule.personality]
                    results.append((rule.personality, adjusted_confidence, description, jobs))
        if not results:
            avg_score = sum(answer_weights.get(answers[qid], 0.5) for qid in answers) / len(answers)
            personality = "Ambivert" if 0.4 <= avg_score <= 0.6 else ("Extrovert" if avg_score > 0.6 else "Introvert")
            description, jobs = self.personality_descriptions[personality]
            results.append((personality, 0.5, description, jobs))
            logging.info(f"Fallback result: {personality} with confidence 0.5")
        return sorted(results, key=lambda x: x[1], reverse=True)[:1]

# QuestionManager
class QuestionManager:
    """Manages personality rules and static questions"""
    def __init__(self, rules_file: str = "rules.json", history_file: str = "history.json"):
        self.rules_file = rules_file
        self.history_file = history_file
        self.rules: List[PersonalityRule] = []
        self.questions: List[Dict[str, Any]] = []
        self.history: List[Dict[str, Any]] = []
        self.load_data()

    def load_data(self):
        try:
            if os.path.exists(self.rules_file):
                with open(self.rules_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.rules = [PersonalityRule.from_dict(rule) for rule in data.get('rules', [])]
            else:
                self.create_sample_rules()
        except Exception as e:
            logging.error(f"Error loading rules: {e}")
            self.create_sample_rules()

        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
        except Exception as e:
            logging.error(f"Error loading history: {e}")

        self.create_sample_questions()

    def save_data(self):
        try:
            with open(self.rules_file, 'w', encoding='utf-8') as f:
                json.dump({'rules': [rule.to_dict() for rule in self.rules]}, f, indent=2, ensure_ascii=False)
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Error saving data: {e}")

    def create_sample_rules(self):
        self.rules = [
            PersonalityRule(
                "RULE001",
                {"q1": " Agree", "q2": "Disagree", "q3": " Agree"},
                "Extrovert",
                0.9
            ),
            PersonalityRule(
                "RULE002",
                {"q4": " Agree", "q5": "Disagree", "q6": " Agree"},
                "Introvert",
                0.85
            ),
            PersonalityRule(
                "RULE003",
                {"q7": "Neutral", "q8": "Neutral", "q9": "Neutral"},
                "Ambivert",
                0.8
            )
        ]
        self.save_data()
        logging.info("Created sample rules")

    def create_sample_questions(self):
        self.questions = [
            # Extrovert Questions
            {"id": "q1", "question": "I enjoy initiating conversations with strangers at events.", "trait": "Extrovert", "weight": 1.2},
            {"id": "q2", "question": "I feel energized after attending social gatherings.", "trait": "Extrovert", "weight": 1.0},
            {"id": "q3", "question": "I prefer working in a team rather than alone.", "trait": "Extrovert", "weight": 1.0},
            # Introvert Questions
            {"id": "q4", "question": "I prefer a quiet evening at home over a lively party.", "trait": "Introvert", "weight": 1.0},
            {"id": "q5", "question": "I need time alone to recharge after social interactions.", "trait": "Introvert", "weight": 1.2},
            {"id": "q6", "question": "I enjoy deep, one-on-one conversations over group chats.", "trait": "Introvert", "weight": 1.0},
            # Ambivert Questions
            {"id": "q7", "question": "I adapt my behavior based on the social context.", "trait": "Ambivert", "weight": 1.0},
            {"id": "q8", "question": "I enjoy both social events and solitary activities equally.", "trait": "Ambivert", "weight": 1.0},
            {"id": "q9", "question": "I can lead or follow depending on the situation.", "trait": "Ambivert", "weight": 1.1}
        ]
        logging.info("Created sample questions")

    def add_rule(self, rule: PersonalityRule) -> bool:
        if not any(r.rule_id == rule.rule_id for r in self.rules):
            self.rules.append(rule)
            self.history.append({
                "action": "create",
                "rule_id": rule.rule_id,
                "timestamp": datetime.now().isoformat(),
                "details": rule.to_dict()
            })
            self.save_data()
            logging.info(f"Added rule: {rule.rule_id}")
            return True
        logging.warning(f"Rule ID {rule.rule_id} already exists")
        return False

    def update_rule(self, rule_id: str, updated_rule: PersonalityRule) -> bool:
        for i, rule in enumerate(self.rules):
            if rule.rule_id == rule_id:
                self.rules[i] = updated_rule
                self.history.append({
                    "action": "update",
                    "rule_id": rule_id,
                    "timestamp": datetime.now().isoformat(),
                    "details": updated_rule.to_dict()
                })
                self.save_data()
                logging.info(f"Updated rule: {rule_id}")
                return True
        logging.warning(f"Rule ID {rule_id} not found for update")
        return False

    def delete_rule(self, rule_id: str) -> bool:
        for i, rule in enumerate(self.rules):
            if rule.rule_id == rule_id:
                deleted_rule = self.rules.pop(i)
                self.history.append({
                    "action": "delete",
                    "rule_id": rule_id,
                    "timestamp": datetime.now().isoformat(),
                    "details": deleted_rule.to_dict()
                })
                self.save_data()
                logging.info(f"Deleted rule: {rule_id}")
                return True
        logging.warning(f"Rule ID {rule_id} not found for deletion")
        return False

    def get_rule(self, rule_id: str) -> Optional[PersonalityRule]:
        return next((rule for rule in self.rules if rule.rule_id == rule_id), None)

    def get_all_rules(self) -> List[PersonalityRule]:
        return self.rules

    def get_all_questions(self) -> List[Dict[str, Any]]:
        return self.questions

# RuleDialog
class RuleDialog(QDialog):
    """Dialog for adding/editing personality rules"""
    def __init__(self, parent=None, rule: PersonalityRule = None, questions: List[Dict[str, Any]] = None):
        super().__init__(parent)
        self.rule = rule
        self.questions = questions or []
        self.setObjectName("ruleDialog")
        self.setWindowTitle("Manage Personality Rule")
        self.setModal(True)
        self.resize(500, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header_label = QLabel("Define Personality Rule")
        header_label.setObjectName("dialogHeader")
        layout.addWidget(header_label)

        # Rule Details Form
        form_group = QGroupBox("Rule Details")
        form_group.setObjectName("ruleDetailsGroup")
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setSpacing(12)
        self.rule_id_edit = QLineEdit()
        self.rule_id_edit.setObjectName("textInput")
        self.rule_id_edit.setPlaceholderText("e.g., RULE004")
        self.personality_combo = QComboBox()
        self.personality_combo.setObjectName("comboBox")
        self.personality_combo.addItems(PERSONALITY_TYPES)
        self.confidence_spin = QSpinBox()
        self.confidence_spin.setObjectName("spinBox")
        self.confidence_spin.setRange(1, 100)
        self.confidence_spin.setValue(80)
        self.confidence_spin.setSuffix("%")
        form_layout.addRow(QLabel("Rule ID:"), self.rule_id_edit)
        form_layout.addRow(QLabel("Personality Type:"), self.personality_combo)
        form_layout.addRow(QLabel("Confidence Level:"), self.confidence_spin)
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # Conditions with Scroll Area
        conditions_group = QGroupBox("Question Conditions")
        conditions_group.setObjectName("conditionsGroup")
        conditions_layout = QVBoxLayout()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QFormLayout()
        scroll_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        scroll_layout.setSpacing(8)
        self.condition_combos = {}
        for question in self.questions:
            qid = question['id']
            label = QLabel(f"Q{qid}: {question['question'][:40]}{'...' if len(question['question']) > 40 else ''}")
            label.setObjectName("conditionLabel")
            label.setToolTip(question['question'])
            label.setMinimumWidth(200)  # Ensure labels have enough space
            combo = QComboBox()
            combo.setObjectName("comboBox")
            combo.addItems([""] + ANSWER_OPTIONS)
            scroll_layout.addRow(label, combo)
            self.condition_combos[qid] = combo
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        conditions_layout.addWidget(scroll_area)
        conditions_group.setLayout(conditions_layout)
        layout.addWidget(conditions_group)

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save Rule")
        save_btn.setObjectName("saveButton")
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("backButton")
        save_btn.clicked.connect(self.validate_and_accept)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        if self.rule:
            self.populate_fields()

    def populate_fields(self):
        self.rule_id_edit.setText(self.rule.rule_id)
        self.rule_id_edit.setReadOnly(True)
        self.personality_combo.setCurrentText(self.rule.personality)
        self.confidence_spin.setValue(int(self.rule.confidence * 100))
        for qid, answer in self.rule.conditions.items():
            if qid in self.condition_combos:
                self.condition_combos[qid].setCurrentText(answer)

    def validate_and_accept(self):
        rule_id = self.rule_id_edit.text().strip()
        if not rule_id:
            QMessageBox.warning(self, "Error", "Rule ID cannot be empty.", QMessageBox.StandardButton.Ok)
            return
        if not self.rule and not rule_id.startswith("RULE"):
            QMessageBox.warning(self, "Error", "Rule ID must start with 'RULE'.", QMessageBox.StandardButton.Ok)
            return
        conditions = {qid: combo.currentText() for qid, combo in self.condition_combos.items() if combo.currentText()}
        if not conditions:
            QMessageBox.warning(self, "Error", "At least one condition must be specified.", QMessageBox.StandardButton.Ok)
            return
        self.accept()

    def get_rule_data(self) -> PersonalityRule:
        conditions = {qid: combo.currentText() for qid, combo in self.condition_combos.items() if combo.currentText()}
        return PersonalityRule(
            self.rule_id_edit.text().strip(),
            conditions,
            self.personality_combo.currentText(),
            self.confidence_spin.value() / 100.0
        )

# HeaderWidget
class HeaderWidget(QWidget):
    """Header widget displaying the app title and navigation buttons"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        title_label = QLabel("Personality Assessment")
        title_label.setObjectName("headerTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.start_button = QPushButton("Start Q/A")
        self.start_button.setObjectName("startButton")
        self.rule_button = QPushButton("Rules Management")
        self.rule_button.setObjectName("ruleButton")
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.rule_button)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

# WelcomePage
# --- Page Classes ---
class WelcomePage(QWidget):
    """Welcome page introducing the personality test with benefits and instructions."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Sets up the welcome page layout with benefits and instruction button."""
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.setContentsMargins(50, 20, 50, 20)
        main_layout.setSpacing(25)

        menu_label = QLabel("Welcome to the Personality Test")
        menu_label.setObjectName("menuLabel")
        menu_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(menu_label)

        # Benefit 1
        benefit1_widget = QWidget()
        benefit1_widget.setObjectName("benefitWidget")
        benefit1_layout = QHBoxLayout(benefit1_widget)
        benefit1_layout.setSpacing(15)

        icon1_label = QLabel()
        icon1_label.setObjectName("benefitIcon")
        icon1_label.setText("🧠")
        icon1_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        benefit1_text = QLabel("Be yourself and answer honestly to find out your personality type.")
        benefit1_text.setObjectName("benefitLabel")
        benefit1_text.setWordWrap(True)

        benefit1_layout.addWidget(icon1_label)
        benefit1_layout.addWidget(benefit1_text)
        main_layout.addWidget(benefit1_widget)

        # Benefit 2
        benefit2_widget = QWidget()
        benefit2_widget.setObjectName("benefitWidget")
        benefit2_layout = QHBoxLayout(benefit2_widget)
        benefit2_layout.setSpacing(15)

        icon2_label = QLabel()
        icon2_label.setObjectName("benefitIcon")
        icon2_label.setText("💡")
        icon2_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        benefit2_text = QLabel("Learn how your personality type influences many areas of your life.")
        benefit2_text.setObjectName("benefitLabel")
        benefit2_text.setWordWrap(True)

        benefit2_layout.addWidget(icon2_label)
        benefit2_layout.addWidget(benefit2_text)
        main_layout.addWidget(benefit2_widget)

        # Benefit 3
        benefit3_widget = QWidget()
        benefit3_widget.setObjectName("benefitWidget")
        benefit3_layout = QHBoxLayout(benefit3_widget)
        benefit3_layout.setSpacing(15)

        icon3_label = QLabel()
        icon3_label.setObjectName("benefitIcon")
        icon3_label.setText("👑")
        icon3_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        benefit3_text = QLabel("Grow into the person you want to be with your optional Premium Suite.")
        benefit3_text.setObjectName("benefitLabel")
        benefit3_text.setWordWrap(True)

        benefit3_layout.addWidget(icon3_label)
        benefit3_layout.addWidget(benefit3_text)
        main_layout.addWidget(benefit3_widget)

        self.instruction_button = QPushButton("View Instructions")
        self.instruction_button.setObjectName("instructionButton")
        main_layout.addWidget(self.instruction_button, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addStretch()
        self.setLayout(main_layout)

# InstructionPage
class InstructionPage(QWidget):
    """Page displaying instructions for taking the personality test"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("instructionPage")
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.setContentsMargins(50, 50, 50, 50)
        main_layout.setSpacing(20)

        label = QLabel("📝 Instructions for Taking the Personality Assessment")
        label.setObjectName("instructionTitleLabel")
        main_layout.addWidget(label)

        instructions = QTextEdit()
        instructions.setReadOnly(True)
        instructions.setObjectName("instructionTextEdit")
        instructions.setText("""
            1. Read each question carefully and select the option that best describes you.
            2. Choose from: Strongly Agree, Agree, Neutral, Disagree, or Strongly Disagree.
            3. You must answer all questions to proceed.
            4. Use Next/Previous buttons to navigate, and Submit on the final question.
            5. Your results will reveal your personality type and career suggestions.
        """)
        main_layout.addWidget(instructions)

        self.back_button = QPushButton("Return to Home")
        self.back_button.setObjectName("backButton")
        main_layout.addWidget(self.back_button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(main_layout)

# QuestionPage
class QuestionPage(QWidget):
    """Page displaying a single question with answer options and navigation buttons"""
    def __init__(self, question: Dict[str, Any], q_number: int, total_questions: int, parent=None):
        super().__init__(parent)
        self.question = question
        self.q_number = q_number
        self.total_questions = total_questions
        self.answer_group = QButtonGroup(self)
        self.radio_buttons = []
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 30, 50, 30)
        main_layout.setSpacing(15)

        q_num_label = QLabel(f"Question {self.q_number} of {self.total_questions}")
        q_num_label.setObjectName("questionNumLabel")
        q_num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(q_num_label)

        q_label = QLabel(self.question['question'])
        q_label.setObjectName("questionLabel")
        q_label.setWordWrap(True)
        main_layout.addWidget(q_label)

        options_group_box = QGroupBox("Select an option:")
        options_group_box.setObjectName("optionsGroup")
        options_layout = QVBoxLayout(options_group_box)
        for option in ANSWER_OPTIONS:
            radio_button = QRadioButton(option)
            radio_button.setObjectName("optionButton")
            radio_button.setAccessibleName(f"Option {option}")
            self.radio_buttons.append(radio_button)
            options_layout.addWidget(radio_button)
            self.answer_group.addButton(radio_button)
        main_layout.addWidget(options_group_box)
        main_layout.addStretch()

        nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("Previous")
        self.prev_button.setObjectName("previousButton")
        self.next_button = QPushButton("Next" if self.q_number < self.total_questions else "Submit")
        self.next_button.setObjectName("nextButton" if self.q_number < self.total_questions else "submitButton")
        nav_layout.addWidget(self.prev_button)
        nav_layout.addStretch()
        nav_layout.addWidget(self.next_button)
        main_layout.addLayout(nav_layout)
        self.setLayout(main_layout)

    def get_selected_answer(self) -> Optional[str]:
        checked_button = self.answer_group.checkedButton()
        return checked_button.text() if checked_button else None

    def set_selected_answer(self, answer_text: str):
        for button in self.radio_buttons:
            if button.text() == answer_text:
                button.setChecked(True)
                break

# ResultPage
class ResultPage(QWidget):
    """Page displaying the test results, personality type, and career suggestions"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(15)

        result_title = QLabel("Assessment Results")
        result_title.setObjectName("resultTitle")
        main_layout.addWidget(result_title)

        self.result_display_label = QLabel()
        self.result_display_label.setObjectName("resultDisplayLabel")
        self.result_display_label.setWordWrap(True)
        main_layout.addWidget(self.result_display_label)

        self.personality_description_label = QLabel()
        self.personality_description_label.setObjectName("personalityDescriptionLabel")
        self.personality_description_label.setWordWrap(True)
        main_layout.addWidget(self.personality_description_label)

        button_layout = QHBoxLayout()
        self.restart_button = QPushButton("Restart Assessment")
        self.restart_button.setObjectName("restartButton")
        button_layout.addWidget(self.restart_button)
        main_layout.addLayout(button_layout)

        main_layout.addStretch()
        self.setLayout(main_layout)

    def show_results(self, questions_list: List[Dict[str, Any]], answers: Dict[str, str]):
        inference_engine = InferenceEngine(self.window().question_manager.get_all_rules(), questions_list)
        predictions = inference_engine.diagnose(answers)
        
        if predictions:
            personality, confidence, description, jobs = predictions[0]
            result_text = f"<b>Your Personality Type: {personality}</b> (Confidence: {confidence:.0%})<br><br>"
            result_text += "<b>Summary of Your Answers:</b><br><br>"
            for qid, answer in answers.items():
                question = next((q for q in questions_list if q['id'] == qid), None)
                if question:
                    result_text += f"{question['question']}: <i>{answer}</i><br>"
            personality_description_text = f"{description}<br><br><b>{jobs}</b>"
            logging.info(f"Generated results: Personality={personality}, Confidence={confidence:.0%}")
        else:
            result_text = "No matching personality found.<br>Please ensure your answers align with known patterns or contact support."
            personality_description_text = ""
            logging.warning("No matching personality found for answers")

        self.result_display_label.setText(result_text)
        self.personality_description_label.setText(personality_description_text)

# RuleManagementPage
class RuleManagementPage(QWidget):
    """Page for managing rules only"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(15)

        title = QLabel("Manage Rules")
        title.setObjectName("ruleTitle")
        main_layout.addWidget(title)

        self.content_stacked_widget = QStackedWidget()
        self.create_page = QWidget()
        self.read_page = QWidget()
        self.update_page = QWidget()
        self.delete_page = QWidget()
        self.history_page = QWidget()
        self.setup_subpages()
        self.content_stacked_widget.addWidget(self.create_page)
        self.content_stacked_widget.addWidget(self.read_page)
        self.content_stacked_widget.addWidget(self.update_page)
        self.content_stacked_widget.addWidget(self.delete_page)
        self.content_stacked_widget.addWidget(self.history_page)

        button_layout = QHBoxLayout()
        buttons = [
            ("Create", self.show_create_page),
            ("Read", self.show_read_page),
            ("Update", self.show_update_page),
            ("Delete", self.show_delete_page),
            ("History", self.show_history_page)
        ]
        for text, slot in buttons:
            btn = QPushButton(text)
            btn.setObjectName("ruleButton-subpage")
            btn.clicked.connect(slot)
            button_layout.addWidget(btn)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.content_stacked_widget)

        back_btn = QPushButton("Return to Home")
        back_btn.setObjectName("backButton")
        back_btn.clicked.connect(self.parent.show_welcome_page)
        main_layout.addWidget(back_btn)
        self.setLayout(main_layout)

    def setup_subpages(self):
        # Create Page
        create_layout = QVBoxLayout(self.create_page)
        create_layout.setSpacing(12)
        create_rule_btn = QPushButton("Add New Rule")
        create_rule_btn.setObjectName("ruleButton1")
        create_rule_btn.clicked.connect(self.create_rule)
        create_layout.addWidget(create_rule_btn)
        create_layout.addStretch()

        # Read Page
        read_layout = QVBoxLayout(self.read_page)
        read_layout.setSpacing(12)
        self.read_table = QTableWidget()
        self.read_table.setObjectName("readTable")
        self.read_table.setColumnCount(4)
        self.read_table.setHorizontalHeaderLabels(["Rule ID", "Personality", "Confidence", "Conditions"])
        header = self.read_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        read_layout.addWidget(self.read_table)

        # Update Page
        update_layout = QVBoxLayout(self.update_page)
        update_layout.setSpacing(12)
        self.update_rule_combo = QComboBox()
        self.update_rule_combo.setObjectName("comboBox")
        update_rule_btn = QPushButton("Edit Selected Rule")
        update_rule_btn.setObjectName("ruleButton3")
        update_rule_btn.clicked.connect(self.update_rule)
        update_layout.addWidget(self.update_rule_combo)
        update_layout.addWidget(update_rule_btn)
        update_layout.addStretch()

        # Delete Page
        delete_layout = QVBoxLayout(self.delete_page)
        delete_layout.setSpacing(12)
        self.delete_rule_combo = QComboBox()
        self.delete_rule_combo.setObjectName("comboBox")
        delete_rule_btn = QPushButton("Delete Selected Rule")
        delete_rule_btn.setObjectName("deleteButton")
        delete_rule_btn.clicked.connect(self.delete_rule)
        delete_layout.addWidget(self.delete_rule_combo)
        delete_layout.addWidget(delete_rule_btn)
        delete_layout.addStretch()

        # History Page
        history_layout = QVBoxLayout(self.history_page)
        history_layout.setSpacing(12)
        self.history_table = QTableWidget()
        self.history_table.setObjectName("historyTable")
        self.history_table.setColumnCount(3)
        self.history_table.setHorizontalHeaderLabels(["Action", "ID", "Timestamp"])
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        reload_btn = QPushButton("Reload Rules")
        reload_btn.setObjectName("ruleButton-subpage")
        reload_btn.clicked.connect(self.reload_data)
        history_layout.addWidget(self.history_table)
        history_layout.addWidget(reload_btn)
        history_layout.addStretch()

    def show_create_page(self):
        self.content_stacked_widget.setCurrentWidget(self.create_page)

    def show_read_page(self):
        self.load_read_table()
        self.content_stacked_widget.setCurrentWidget(self.read_page)

    def show_update_page(self):
        self.load_update_combos()
        self.content_stacked_widget.setCurrentWidget(self.update_page)

    def show_delete_page(self):
        self.load_delete_combos()
        self.content_stacked_widget.setCurrentWidget(self.delete_page)

    def show_history_page(self):
        self.load_history_table()
        self.content_stacked_widget.setCurrentWidget(self.history_page)

    def create_rule(self):
        dialog = RuleDialog(self, questions=self.parent.question_manager.get_all_questions())
        if dialog.exec() == QDialog.DialogCode.Accepted:
            rule = dialog.get_rule_data()
            if self.parent.question_manager.add_rule(rule):
                QMessageBox.information(self, "Success", "Rule added successfully!", QMessageBox.StandardButton.Ok)
            else:
                QMessageBox.warning(self, "Error", "Rule ID already exists or invalid!", QMessageBox.StandardButton.Ok)

    def load_read_table(self):
        rules = self.parent.question_manager.get_all_rules()
        self.read_table.setRowCount(len(rules))
        for row, rule in enumerate(rules):
            self.read_table.setItem(row, 0, QTableWidgetItem(rule.rule_id))
            self.read_table.setItem(row, 1, QTableWidgetItem(rule.personality))
            self.read_table.setItem(row, 2, QTableWidgetItem(f"{rule.confidence:.0%}"))
            conditions = ", ".join([f"Q{k}: {v}" for k, v in rule.conditions.items()])
            self.read_table.setItem(row, 3, QTableWidgetItem(conditions))

    def load_update_combos(self):
        self.update_rule_combo.clear()
        rules = self.parent.question_manager.get_all_rules()
        for rule in rules:
            self.update_rule_combo.addItem(f"{rule.rule_id} - {rule.personality}")

    def update_rule(self):
        if self.update_rule_combo.currentIndex() >= 0:
            rule_id = self.update_rule_combo.currentText().split(" - ")[0]
            rule = self.parent.question_manager.get_rule(rule_id)
            if rule:
                dialog = RuleDialog(self, rule, self.parent.question_manager.get_all_questions())
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    updated_rule = dialog.get_rule_data()
                    if self.parent.question_manager.update_rule(rule_id, updated_rule):
                        QMessageBox.information(self, "Success", "Rule updated successfully!", QMessageBox.StandardButton.Ok)
                        self.load_update_combos()

    def load_delete_combos(self):
        self.delete_rule_combo.clear()
        rules = self.parent.question_manager.get_all_rules()
        for rule in rules:
            self.delete_rule_combo.addItem(f"{rule.rule_id} - {rule.personality}")

    def delete_rule(self):
        if self.delete_rule_combo.currentIndex() >= 0:
            rule_id = self.delete_rule_combo.currentText().split(" - ")[0]
            reply = QMessageBox.question(self, "Confirm", f"Are you sure you want to delete rule {rule_id}?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                if self.parent.question_manager.delete_rule(rule_id):
                    QMessageBox.information(self, "Success", "Rule deleted successfully!", QMessageBox.StandardButton.Ok)
                    self.load_delete_combos()

    def load_history_table(self):
        history = self.parent.question_manager.history
        self.history_table.setRowCount(len(history))
        for row, entry in enumerate(history):
            self.history_table.setItem(row, 0, QTableWidgetItem(entry['action']))
            self.history_table.setItem(row, 1, QTableWidgetItem(entry.get('rule_id', '')))
            self.history_table.setItem(row, 2, QTableWidgetItem(entry['timestamp'][:19]))

    def reload_data(self):
        self.parent.question_manager.load_data()
        QMessageBox.information(self, "Success", "Rules reloaded successfully!", QMessageBox.StandardButton.Ok)

# PersonalityTestApp
class PersonalityTestApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Personality Assessment")
        self.setGeometry(100, 100, 900, 700)
        self.question_manager = QuestionManager()
        self.questions = self.question_manager.get_all_questions()
        self.answers: Dict[str, str] = {}
        self.init_ui()

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.header_widget = HeaderWidget(self)
        self.header_widget.start_button.clicked.connect(self.show_question_page)
        self.header_widget.rule_button.clicked.connect(self.show_rule_management_page)
        main_layout.addWidget(self.header_widget)

        self.stacked_widget = QStackedWidget()
        self.welcome_page = WelcomePage(self)
        self.instruction_page = InstructionPage(self)
        self.result_page = ResultPage(self)
        self.rule_management_page = RuleManagementPage(self)
        self.welcome_page.instruction_button.clicked.connect(self.show_instruction_page)
        self.instruction_page.back_button.clicked.connect(self.show_welcome_page)
        self.result_page.restart_button.clicked.connect(self.restart_test)
        self.stacked_widget.addWidget(self.welcome_page)
        self.stacked_widget.addWidget(self.instruction_page)
        self.create_question_pages()
        self.stacked_widget.addWidget(self.result_page)
        self.stacked_widget.addWidget(self.rule_management_page)
        main_layout.addWidget(self.stacked_widget)

        self.apply_styles()

    def create_question_pages(self):
        for i in range(2, self.stacked_widget.count() - 2):
            self.stacked_widget.removeWidget(self.stacked_widget.widget(i))
        self.questions = self.question_manager.get_all_questions()
        for i, question in enumerate(self.questions, 2):
            page = QuestionPage(question, i - 1, len(self.questions), self)
            page.prev_button.clicked.connect(self.go_previous)
            page.next_button.clicked.connect(self.go_next if i - 1 < len(self.questions) else self.submit_test)
            self.stacked_widget.insertWidget(i, page)

    def show_welcome_page(self):
        self.stacked_widget.setCurrentIndex(0)
        self.answers.clear()

    def show_instruction_page(self):
        self.stacked_widget.setCurrentIndex(1)

    def show_question_page(self, index: int = 0):
        if index + 2 < self.stacked_widget.count():
            self.stacked_widget.setCurrentIndex(index + 2)
            page = self.stacked_widget.widget(index + 2)
            if page.question['id'] in self.answers:
                page.set_selected_answer(self.answers[page.question['id']])
        else:
            logging.error(f"Invalid question index: {index}")
            QMessageBox.warning(self, "Error", "No more questions available.", QMessageBox.StandardButton.Ok)

    def show_result_page(self):
        self.result_page.show_results(self.questions, self.answers)
        self.stacked_widget.setCurrentIndex(len(self.questions) + 2)

    def show_rule_management_page(self):
        self.stacked_widget.setCurrentIndex(len(self.questions) + 3)

    def go_next(self):
        current_index = self.stacked_widget.currentIndex()
        current_page = self.stacked_widget.currentWidget()
        answer = current_page.get_selected_answer()
        if answer:
            self.answers[current_page.question['id']] = answer
            self.show_question_page(current_index - 1)
        else:
            QMessageBox.warning(self, "Warning", "Please select an option before continuing.", QMessageBox.StandardButton.Ok)

    def go_previous(self):
        current_index = self.stacked_widget.currentIndex()
        current_page = self.stacked_widget.currentWidget()
        answer = current_page.get_selected_answer()
        if answer:
            self.answers[current_page.question['id']] = answer
        if current_index > 2:
            self.show_question_page(current_index - 3)

    def submit_test(self):
        current_index = self.stacked_widget.currentIndex()
        current_page = self.stacked_widget.currentWidget()
        answer = current_page.get_selected_answer()
        if answer:
            self.answers[current_page.question['id']] = answer
            if len(self.answers) == len(self.questions):
                self.show_result_page()
            else:
                missing = [q['id'] for q in self.questions if q['id'] not in self.answers]
                QMessageBox.warning(self, "Warning", f"Please answer all questions. Missing answers for questions: {', '.join(missing)}.", QMessageBox.StandardButton.Ok)
        else:
            QMessageBox.warning(self, "Warning", "Please select an option before submitting.", QMessageBox.StandardButton.Ok)

    def restart_test(self):
        self.answers.clear()
        self.stacked_widget.setCurrentIndex(0)
        for i in range(2, len(self.questions) + 2):
            page = self.stacked_widget.widget(i)
            if isinstance(page, QuestionPage):
                page.answer_group.setExclusive(False)
                for button in page.radio_buttons:
                    button.setChecked(False)
                page.answer_group.setExclusive(True)

    def apply_styles(self):
        self.setStyleSheet("""
            * {
                font-family: "Segoe UI", sans-serif;
                font-size: 20px;
                color: #2c3e50;
            }
            QMainWindow {
                background-color: #f0f4f8;
            }
            HeaderWidget {
                background-color: #ffffff;
                border-bottom: 2px solid #e0e6ed;
                padding: 20px;
            }
            #headerTitle {
                font-size: 30px;
                font-weight: 700;
                color: #1a3c34;
            }
            #menuLabel {
                font-size: 28px;
                font-weight: 600;
                color: #1a3c34;
                padding: 12px;
            }
            /* Benefit Widgets Styling */
            QWidget#benefitWidget {
                background-color: #d1e8d9;
                border-radius: 15px;
                padding: 15px;
                margin: -3px 5px;
                max-width: 650px;
                min-width: 400px;
                border: 1px solid #b7d7c1;
            }
            QLabel#benefitLabel {
                font-size: 20px;
                color: #2c3e50;
                padding: 0;
            }
            QLabel#benefitIcon {
                font-size: 40px;
                font-weight: bold;
                color: #3498db;
                margin-right: 15px;
                min-width: 40px;
                max-width: 40px;
            }
            #instructionButton {
                background-color: #1e88e5;
                color: #ffffff;
                font-size: 18px;
                font-weight: 600;
                padding: 12px;
                border-radius: 8px;
                min-width: 220px;
                border: none;
                transition: background-color 0.2s;
            }
            #instructionButton:hover {
                background-color: #1565c0;
            }
            #instructionPage {
                background-color: #ffffff;
                border-radius: 12px;
                margin: 20px;
                padding: 20px;
            }
            QLabel#instructionTitleLabel {
                font-size: 28px;
                font-weight: 600;
                color: #1a3c34;
                padding: 10px;
            }
            QTextEdit#instructionTextEdit {
                background-color: #f9fafb;
                border: 1px solid #d0dcea;
                border-radius: 8px;
                padding: 15px;
                font-size: 18px;
            }
            QPushButton {
                padding: 10px 20px;
                border-radius: 8px;
                border: none;
                color: white;
                font-weight: 600;
                font-size: 18px;
                min-width: 140px;
                transition: background-color 0.2s, transform 0.1s;
            }
            QPushButton:hover {
                transform: scale(1.02);
            }
            #startButton {
                font-size: 22px;
                background-color: #2ecc71;
            }
            #startButton:hover {
                background-color: #27ae60;
            }
            #ruleButton {
                font-size: 22px;
                background-color: #26c6da;
            }
            #ruleButton:hover {
                background-color: #0097a7;
            }
            #backButton {
                background-color: #ef5350;
            }
            #backButton:hover {
                background-color: #d32f2f;
            }
            #previousButton {
                background-color: #f1c40f;
            }
            #previousButton:hover {
                background-color: #d4ac0d;
            }
            #nextButton {
                background-color: #1e88e5;
            }
            #nextButton:hover {
                background-color: #1565c0;
            }
            #submitButton {
                background-color: #2ecc71;
            }
            #submitButton:hover {
                background-color: #27ae60;
            }
            #restartButton {
                
                background-color: #1e88e5;
            }
            #restartButton:hover {
                background-color: #1565c0;
            }
            #ruleButton1, #ruleButton3 {
                background-color: #f1c40f;
            }
            #ruleButton1:hover, #ruleButton3:hover {
                background-color: #d4ac0d;
            }
            #ruleButton-subpage {
                background-color: #1e88e5;
            }
            #ruleButton-subpage:hover {
                background-color: #1565c0;
            }
            #saveButton {
                background-color: #2ecc71;
            }
            #saveButton:hover {
                background-color: #27ae60;
            }
            #deleteButton {
                background-color: #ef5350;
            }
            #deleteButton:hover {
                background-color: #d32f2f;
            }
            QGroupBox#optionsGroup {
                background-color: #e6f0fa;
                font-size: 18px;
                font-weight: 600;
                margin-top: 10px;
                border: 1px solid #d0dcea;
                border-radius: 8px;
                padding: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
                background-color: #f0f4f8;
            }
            QRadioButton {
                padding: 10px;
                font-size: 18px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            #questionNumLabel {
                font-size: 18px;
                color: #7f8c8d;
            }
            #questionLabel {
                font-size: 22px;
                font-weight: 600;
                min-height: 80px;
                color: #1a3c34;
                qproperty-alignment: AlignCenter;
            }
            #resultTitle {
                font-size: 28px;
                font-weight: 600;
                color: #1a3c34;
            }
            #resultDisplayLabel {
                font-size: 16px;
                color: #34495e;
            }
            #personalityDescriptionLabel {
                font-size: 18px;
                color: #2c3e50;
            }
            #ruleTitle {
                font-size: 26px;
                font-weight: 600;
                color: #1a3c34;
            }
            QGroupBox#ruleDetailsGroup, QGroupBox#conditionsGroup {
                background-color: #ffffff;
                border: 1px solid #d0dcea;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                padding: 15px;
            }
            #dialogHeader {
                font-size: 24px;
                font-weight: 700;
                color: #1a3c34;
                padding: 10px;
                text-align: center;
            }
            QLabel#conditionLabel {
                font-size: 16px;
                color: #2c3e50;
                min-width: 200px;
            }
            QLineEdit#textInput {
                padding: 10px;
                border-radius: 6px;
                border: 1px solid #d0dcea;
                font-size: 16px;
                min-width: 250px;
            }
            QComboBox#comboBox {
                padding: 10px;
                border-radius: 6px;
                border: 1px solid #d0dcea;
                font-size: 16px;
                min-width: 250px;
            }
            QSpinBox#spinBox {
                padding: 10px;
                border-radius: 6px;
                border: 1px solid #d0dcea;
                font-size: 16px;
                min-width: 100px;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollArea QWidget {
                padding: 10px;
            }
            QTableWidget#readTable, QTableWidget#historyTable {
                background-color: #ffffff;
                border: 1px solid #d0dcea;
                border-radius: 8px;
                gridline-color: #b0bec5;
                font-size: 16px;
            }
            QHeaderView::section {
                background-color: #1a3c34;
                color: white;
                padding: 6px;
                border: 1px solid #b0bec5;
                font-weight: 600;
            }
        """)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = PersonalityTestApp()
    ex.show()
    sys.exit(app.exec())