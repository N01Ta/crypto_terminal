# src/core/auth_service.py
import requests
import json
import os
# load_dotenv теперь не нужен здесь, если config.py его уже вызвал
# и переменные окружения доступны глобально через os.environ



class AuthService:
    def __init__(self, base_url):
        self.base_url = base_url
        self.register_url = f"{self.base_url}/auth/register"
        self.login_url = f"{self.base_url}/auth/login"
        self.check_version_url = f"{self.base_url}/sec/check_version"
        if not self.base_url.startswith("http"): # Простая проверка, что URL загрузился
             print(f"Warning: BACKEND_BASE_URL in AuthService might not be loaded correctly: {self.base_url}")
        print(f"AuthService initialized with backend URL: {self.base_url}")

    def check_client_version(self, client_version_str: str):
        payload = {"client_version": client_version_str}
        try:
            print(f"Checking client version at {self.check_version_url} with payload: {payload}")
            response = requests.post(self.check_version_url, json=payload, timeout=5)

            if response.status_code == 200:
                response_data = response.json()
                print(f"Client version check OK: {response_data.get('message')}")
                return True, response_data.get("message", "Версия клиента актуальна.")
            elif response.status_code == 426: # Upgrade Required
                error_detail = "Требуется обновление"
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        error_detail = error_data["detail"]
                except json.JSONDecodeError:
                    pass
                print(f"Client version outdated: {error_detail}")
                return False, error_detail
            else:
                # Для других кодов ошибок, которые не являются 200 или 426
                error_detail = f"Неожиданный ответ сервера: {response.status_code}"
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        error_detail = error_data["detail"]
                except json.JSONDecodeError:
                     error_detail += f". Ответ: {response.text[:200]}"
                print(f"Error during version check: {error_detail}")
                return False, error_detail

        except requests.exceptions.RequestException as req_err:
            print(f"Request error during version check: {req_err}")
            return False, f"Ошибка сети или подключения при проверке версии: {req_err}"
        except Exception as e:
            print(f"Unexpected error during version check: {e}")
            return False, f"Непредвиденная ошибка при проверке версии: {e}"

    def register_user(self, service_login, service_password, mexc_api_key, mexc_api_secret):
        payload = {
            "login": service_login,
            "password": service_password,
            "mexc_api_key": mexc_api_key,
            "mexc_api_secret": mexc_api_secret
        }
        try:
            print(f"Registering user at {self.register_url} with payload: {json.dumps(payload, indent=2)}")
            response = requests.post(self.register_url, json=payload, timeout=10)
            response.raise_for_status() # Вызовет исключение для 4xx/5xx
            user_data = response.json()
            print(f"Registration successful: {user_data}")
            return user_data, None
        except requests.exceptions.HTTPError as http_err:
            error_detail = "Ошибка регистрации"
            try:
                error_data = http_err.response.json()
                error_detail = error_data.get("detail", error_detail)
            except json.JSONDecodeError:
                error_detail = f"Ошибка сервера: {http_err.response.status_code}. Ответ: {http_err.response.text[:200]}"
            print(f"HTTP error during registration: {error_detail} (Status: {http_err.response.status_code})")
            return None, error_detail
        except requests.exceptions.RequestException as req_err:
            print(f"Request error during registration: {req_err}")
            return None, f"Ошибка сети или подключения: {req_err}"
        except Exception as e:
            print(f"Unexpected error during registration: {e}")
            return None, f"Непредвиденная ошибка: {e}"

    def login_user(self, service_login, service_password):
        payload = {"login": service_login, "password": service_password}
        try:
            print(f"Logging in user at {self.login_url} with payload (form-data): {payload}")
            response = requests.post(self.login_url, data=payload, timeout=10)
            response.raise_for_status()
            user_data = response.json()
            print(f"Login successful: {user_data}")
            return user_data, None
        except requests.exceptions.HTTPError as http_err:
            error_detail = "Ошибка входа"
            try:
                error_data = http_err.response.json()
                error_detail = error_data.get("detail", error_detail)
            except json.JSONDecodeError:
                error_detail = f"Ошибка сервера: {http_err.response.status_code}. Ответ: {http_err.response.text[:200]}"
            print(f"HTTP error during login: {error_detail} (Status: {http_err.response.status_code})")
            return None, error_detail
        except requests.exceptions.RequestException as req_err:
            print(f"Request error during login: {req_err}")
            return None, f"Ошибка сети или подключения: {req_err}"
        except Exception as e:
            print(f"Unexpected error during login: {e}")
            return None, f"Непредвиденная ошибка: {e}"