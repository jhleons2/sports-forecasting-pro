import requests
import json
from datetime import datetime, timedelta
import time
import os

class RealFixturesAPI:
    """API para obtener partidos reales de fútbol usando únicamente datos reales"""
    
    def __init__(self):
        # Usar API gratuita de Football-Data.org con tu API key
        self.api_key = os.environ.get('FOOTBALL_API_KEY', '2b1693b0c9ba4a99bf8346cd0a9d27d0')  # Tu API key
        self.base_url = "https://api.football-data.org/v4"
        self.headers = {
            'X-Auth-Token': self.api_key,
            'Content-Type': 'application/json'
        }
        
        # IDs de las principales ligas europeas (según tu cuenta)
        self.league_ids = {
            'E0': 'PL',  # Premier League
            'SP1': 'PD', # Primera Division (La Liga)
            'D1': 'BL1', # Bundesliga
            'I1': 'SA',  # Serie A
            'F1': 'FL1'  # Ligue 1
        }
        
        # Cache para evitar múltiples llamadas
        self.cache = {}
        self.last_request_time = 0
        self.request_delay = 6  # 6 segundos entre requests para respetar límite
        
        print(f"🔑 API configurada con key: {self.api_key[:8]}...")
        print(f"⏱️ Delay entre requests: {self.request_delay} segundos")
        
    def _respect_rate_limit(self):
        """Respetar el límite de requests de la API"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.request_delay:
            wait_time = self.request_delay - time_since_last_request
            print(f"⏳ Esperando {wait_time:.1f} segundos para respetar límite de API...")
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def get_upcoming_matches(self, days_ahead=7):
        """Obtener partidos próximos de múltiples fuentes gratuitas - SOLO DATOS REALES"""
        try:
            # Verificar cache primero
            cache_key = f"api_fixtures_{days_ahead}"
            if cache_key in self.cache:
                cache_time = self.cache[cache_key]['timestamp']
                if time.time() - cache_time < 600:  # Cache válido por 10 minutos
                    print(f"📋 Usando datos del cache para {days_ahead} días")
                    return self.cache[cache_key]['data']
            
            print(f"🔍 Obteniendo partidos REALES de fuentes gratuitas para {days_ahead} días...")
            
            # Intentar múltiples fuentes gratuitas
            fixtures = []
            
            # Fuente 1: Football-Data.org (si tienes API key)
            if self.api_key:
                try:
                    self._respect_rate_limit()
                    football_data_fixtures = self._get_football_data_matches(days_ahead)
                    if len(football_data_fixtures) > 0:
                        fixtures.extend(football_data_fixtures)
                        print(f"✅ Obtenidos {len(football_data_fixtures)} partidos de Football-Data.org")
                except Exception as e:
                    print(f"⚠️ Error con Football-Data.org: {e}")
            
            # Fuente 2: The Sport DB (completamente gratuito)
            try:
                sportdb_fixtures = self._get_sportdb_matches(days_ahead)
                if len(sportdb_fixtures) > 0:
                    fixtures.extend(sportdb_fixtures)
                    print(f"✅ Obtenidos {len(sportdb_fixtures)} partidos de The Sport DB (League)")
                
                # También intentar método diario para más cobertura
                sportdb_daily_fixtures = self._get_sportdb_daily_matches(days_ahead)
                if len(sportdb_daily_fixtures) > 0:
                    fixtures.extend(sportdb_daily_fixtures)
                    print(f"✅ Obtenidos {len(sportdb_daily_fixtures)} partidos de The Sport DB (Daily)")
                    
            except Exception as e:
                print(f"⚠️ Error con The Sport DB: {e}")
            
            # Fuente 3: FootyStats (gratuito con límite)
            try:
                footystats_fixtures = self._get_footystats_matches(days_ahead)
                if len(footystats_fixtures) > 0:
                    fixtures.extend(footystats_fixtures)
                    print(f"✅ Obtenidos {len(footystats_fixtures)} partidos de FootyStats")
            except Exception as e:
                print(f"⚠️ Error con FootyStats: {e}")
            
            # Eliminar duplicados basado en equipos y fecha
            unique_fixtures = self._remove_duplicates(fixtures)
            
            if len(unique_fixtures) > 0:
                # Guardar en cache
                self.cache[cache_key] = {
                    'data': unique_fixtures,
                    'timestamp': time.time()
                }
                print(f"🎯 Total de partidos REALES únicos obtenidos: {len(unique_fixtures)}")
                return unique_fixtures
            else:
                print("❌ No se pudieron obtener partidos de ninguna fuente")
                return []
            
        except Exception as e:
            print(f"❌ Error obteniendo datos: {e}")
            return []
    
    def test_api_connection(self):
        """Probar la conexión con la API y verificar ligas disponibles"""
        try:
            print(f"🔍 Probando conexión API con key: {self.api_key[:8]}...")
            
            # Probar endpoint de competencias
            url = f"{self.base_url}/competitions"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                competitions = response.json()
                print(f"✅ API conectada. Competencias disponibles:")
                
                available_leagues = []
                for comp in competitions.get('competitions', []):
                    if comp.get('plan') == 'TIER_ONE':  # Solo ligas principales
                        available_leagues.append({
                            'id': comp['id'],
                            'name': comp['name'],
                            'code': comp.get('code', 'N/A')
                        })
                        print(f"  - {comp['name']} (ID: {comp['id']}, Code: {comp.get('code', 'N/A')})")
                
                return {
                    'success': True,
                    'available_leagues': available_leagues,
                    'total_competitions': len(competitions.get('competitions', []))
                }
            else:
                print(f"❌ Error API: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            print(f"❌ Error conectando API: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_football_data_matches(self, days_ahead):
        """Obtener partidos reales usando Football-Data.org API - SOLO DATOS REALES"""
        fixtures = []
        today = datetime.now().date()
        date_to = today + timedelta(days=days_ahead)
        
        print(f"📡 Consultando API Football-Data.org desde {today} hasta {date_to}")
        
        for league_code, league_id in self.league_ids.items():
            try:
                print(f"🔍 Obteniendo partidos para {league_code} ({league_id})...")
                
                url = f"{self.base_url}/competitions/{league_id}/matches"
                params = {
                    'dateFrom': today.isoformat(),
                    'dateTo': date_to.isoformat(),
                    'status': 'SCHEDULED'
                }
                
                response = requests.get(url, headers=self.headers, params=params, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    matches = data.get('matches', [])
                    print(f"📊 Respuesta API: {len(matches)} partidos encontrados para {league_code}")
                    
                    for match in matches:
                        if match['status'] == 'SCHEDULED':
                            match_date = datetime.fromisoformat(match['utcDate'].replace('Z', '+00:00'))
                            fixtures.append({
                                'HomeTeam': match['homeTeam']['name'],
                                'AwayTeam': match['awayTeam']['name'],
                                'Date': match_date.strftime('%Y-%m-%d'),
                                'Time': match_date.strftime('%H:%M'),
                                'League': league_code,
                                'Competition': match['competition']['name'],
                                'Status': match['status'],
                                'Source': 'Football-Data.org API'
                            })
                    
                    print(f"✅ Agregados {len([m for m in matches if m['status'] == 'SCHEDULED'])} partidos programados para {league_code}")
                    
                elif response.status_code == 429:
                    print(f"⚠️ Límite de requests alcanzado para {league_code}")
                    print("⏳ Esperando 10 segundos antes de continuar...")
                    time.sleep(10)
                    continue
                    
                elif response.status_code == 403:
                    print(f"❌ Acceso denegado para {league_code} - verifica tu API key")
                    continue
                    
                else:
                    print(f"⚠️ Error API {league_code}: {response.status_code} - {response.text}")
                
                # Respetar límite de requests entre ligas
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Error obteniendo partidos de {league_code}: {e}")
                continue
        
        print(f"🎯 Total de partidos REALES obtenidos de API: {len(fixtures)}")
        return fixtures
    
    def _get_sportdb_matches(self, days_ahead):
        """Obtener partidos de The Sport DB - COMPLETAMENTE GRATUITO usando documentación oficial"""
        print("📡 Consultando The Sport DB (gratuito) usando endpoints oficiales...")
        fixtures = []
        today = datetime.now().date()
        
        # IDs de ligas principales - CORREGIDOS según The Sports DB
        sportdb_leagues = {
            'E0': '4328',  # Premier League (verificar si es correcto)
            'SP1': '4335', # La Liga  
            'D1': '4331',  # Bundesliga
            'I1': '4332',  # Serie A
            'F1': '4334'   # Ligue 1
        }
        
        # Primero verificar qué liga es realmente el ID 4328
        print("🔍 Verificando ID de liga 4328...")
        test_url = f"https://www.thesportsdb.com/api/v1/json/123/lookupleague.php?id=4328"
        try:
            test_response = requests.get(test_url, timeout=10)
            if test_response.status_code == 200:
                test_data = test_response.json()
                league_info = test_data.get('leagues', [{}])[0]
                league_name = league_info.get('strLeague', 'Unknown')
                print(f"📊 ID 4328 corresponde a: {league_name}")
                
                # Si no es Premier League, buscar el ID correcto
                if 'Premier League' not in league_name:
                    print("⚠️ ID 4328 no es Premier League, buscando ID correcto...")
                    # Buscar Premier League en la lista de ligas
                    all_leagues_url = "https://www.thesportsdb.com/api/v1/json/123/all_leagues.php"
                    leagues_response = requests.get(all_leagues_url, timeout=10)
                    if leagues_response.status_code == 200:
                        leagues_data = leagues_response.json()
                        all_leagues = leagues_data.get('leagues', [])
                        
                        for league in all_leagues:
                            if 'Premier League' in league.get('strLeague', ''):
                                correct_id = league.get('idLeague', '')
                                print(f"✅ Premier League ID correcto: {correct_id}")
                                sportdb_leagues['E0'] = correct_id
                                break
        except Exception as e:
            print(f"⚠️ Error verificando IDs de ligas: {e}")
        
        # Usar el endpoint oficial para próximos partidos de liga
        for league_code, league_id in sportdb_leagues.items():
            try:
                print(f"🔍 Obteniendo próximos partidos de {league_code} (ID: {league_id})...")
                
                # Endpoint oficial: Schedule League Next
                url = f"https://www.thesportsdb.com/api/v1/json/123/eventsnextleague.php?id={league_id}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    events = data.get('events', [])
                    
                    print(f"📊 Respuesta The Sport DB: {len(events)} eventos encontrados para {league_code}")
                    
                    for event in events:
                        try:
                            event_date = datetime.strptime(event['dateEvent'], '%Y-%m-%d').date()
                            
                            # Solo partidos futuros dentro del rango
                            if today <= event_date <= today + timedelta(days=days_ahead):
                                fixtures.append({
                                    'HomeTeam': event['strHomeTeam'],
                                    'AwayTeam': event['strAwayTeam'],
                                    'Date': event['dateEvent'],
                                    'Time': event.get('strTime', '15:00'),
                                    'League': league_code,
                                    'Competition': event.get('strLeague', 'Unknown'),
                                    'Status': 'SCHEDULED',
                                    'Source': 'The Sport DB (Official)',
                                    'EventID': event.get('idEvent', ''),
                                    'Venue': event.get('strVenue', ''),
                                    'Country': event.get('strCountry', '')
                                })
                        except Exception as e:
                            print(f"⚠️ Error procesando evento: {e}")
                            continue
                    
                    valid_events = len([e for e in events if today <= datetime.strptime(e['dateEvent'], '%Y-%m-%d').date() <= today + timedelta(days=days_ahead)])
                    print(f"✅ Agregados {valid_events} partidos válidos de {league_code}")
                
                elif response.status_code == 429:
                    print(f"⚠️ Límite de requests alcanzado para {league_code}")
                    time.sleep(5)
                    continue
                else:
                    print(f"⚠️ Error API {league_code}: {response.status_code}")
                
                # Respetar límite de requests (30 por minuto para usuarios gratuitos)
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Error obteniendo {league_code} de The Sport DB: {e}")
                continue
        
        print(f"📊 Total partidos de The Sport DB: {len(fixtures)}")
        return fixtures
    
    def _get_sportdb_daily_matches(self, days_ahead):
        """Obtener partidos por día usando The Sport DB - Endpoint Schedule Day"""
        print("📅 Consultando The Sport DB por días específicos...")
        fixtures = []
        today = datetime.now().date()
        
        # Obtener partidos para cada día en el rango
        for day_offset in range(days_ahead + 1):
            target_date = today + timedelta(days=day_offset)
            date_str = target_date.strftime('%Y-%m-%d')
            
            try:
                print(f"🔍 Obteniendo partidos para {date_str}...")
                
                # Endpoint oficial: Schedule Day
                url = f"https://www.thesportsdb.com/api/v1/json/123/eventsday.php?d={date_str}&s=Soccer"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    events = data.get('events', [])
                    
                    for event in events:
                        try:
                            # Mapear ligas según el nombre
                            league_name = event.get('strLeague', '')
                            league_code = self._map_league_name_to_code(league_name)
                            
                            if league_code:  # Solo incluir ligas que conocemos
                                fixtures.append({
                                    'HomeTeam': event['strHomeTeam'],
                                    'AwayTeam': event['strAwayTeam'],
                                    'Date': event['dateEvent'],
                                    'Time': event.get('strTime', '15:00'),
                                    'League': league_code,
                                    'Competition': league_name,
                                    'Status': 'SCHEDULED',
                                    'Source': 'The Sport DB (Daily)',
                                    'EventID': event.get('idEvent', ''),
                                    'Venue': event.get('strVenue', ''),
                                    'Country': event.get('strCountry', '')
                                })
                        except Exception as e:
                            continue
                    
                    print(f"✅ Obtenidos {len(events)} eventos para {date_str}")
                
                elif response.status_code == 429:
                    print(f"⚠️ Límite de requests alcanzado para {date_str}")
                    time.sleep(5)
                    continue
                
                # Respetar límite de requests
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Error obteniendo partidos para {date_str}: {e}")
                continue
        
        print(f"📊 Total partidos diarios de The Sport DB: {len(fixtures)}")
        return fixtures
    
    def _map_league_name_to_code(self, league_name):
        """Mapear nombres de ligas a códigos estándar - MEJORADO"""
        league_mapping = {
            # Premier League
            'English Premier League': 'E0',
            'Premier League': 'E0',
            'EPL': 'E0',
            
            # La Liga
            'La Liga': 'SP1',
            'Primera Division': 'SP1',
            'Spanish La Liga': 'SP1',
            
            # Bundesliga
            'Bundesliga': 'D1',
            'German Bundesliga': 'D1',
            
            # Serie A
            'Serie A': 'I1',
            'Italian Serie A': 'I1',
            
            # Ligue 1
            'Ligue 1': 'F1',
            'French Ligue 1': 'F1',
            
            # Champions League
            'Champions League': 'CL',
            'UEFA Champions League': 'CL',
            
            # Europa League
            'Europa League': 'EL',
            'UEFA Europa League': 'EL',
            
            # Evitar League One y Championship
            'League One': None,
            'Championship': None,
            'League Two': None
        }
        
        league_name_lower = league_name.lower()
        
        for key, code in league_mapping.items():
            if key.lower() in league_name_lower:
                return code
        
        # Si no encuentra coincidencia, retornar None para evitar ligas desconocidas
        print(f"⚠️ Liga no reconocida: {league_name}")
        return None
    
    def _get_footystats_matches(self, days_ahead):
        """Obtener partidos de FootyStats - GRATUITO CON LÍMITE"""
        print("📡 Consultando FootyStats (gratuito con límite)...")
        fixtures = []
        
        try:
            # FootyStats tiene un endpoint gratuito limitado
            url = "https://api.footystats.org/api/v1/league/upcoming-matches"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                matches = data.get('data', [])
                
                today = datetime.now().date()
                for match in matches[:20]:  # Limitar a 20 partidos
                    try:
                        match_date = datetime.strptime(match['date'], '%Y-%m-%d').date()
                        
                        if today <= match_date <= today + timedelta(days=days_ahead):
                            fixtures.append({
                                'HomeTeam': match['homeTeam']['name'],
                                'AwayTeam': match['awayTeam']['name'],
                                'Date': match['date'],
                                'Time': match.get('time', '15:00'),
                                'League': match.get('league', {}).get('name', 'Unknown'),
                                'Competition': match.get('league', {}).get('name', 'Unknown'),
                                'Status': 'SCHEDULED',
                                'Source': 'FootyStats'
                            })
                    except Exception as e:
                        continue
                
                print(f"✅ Obtenidos {len(fixtures)} partidos de FootyStats")
            
        except Exception as e:
            print(f"❌ Error con FootyStats: {e}")
        
        return fixtures
    
    def _remove_duplicates(self, fixtures):
        """Eliminar partidos duplicados basado en equipos y fecha"""
        unique_fixtures = []
        seen = set()
        
        for fixture in fixtures:
            # Crear clave única basada en equipos y fecha
            key = f"{fixture['HomeTeam']}_{fixture['AwayTeam']}_{fixture['Date']}"
            
            if key not in seen:
                seen.add(key)
                unique_fixtures.append(fixture)
        
        print(f"🔄 Eliminados {len(fixtures) - len(unique_fixtures)} duplicados")
        return unique_fixtures
    
    def _get_free_api_matches(self, days_ahead):
        """Usar API completamente gratuita sin key"""
        try:
            # Usar API gratuita de RapidAPI
            return self._get_rapidapi_matches(days_ahead)
        except Exception as e:
            print(f"Error con API gratuita: {e}")
            # Último recurso: usar datos de calendario oficial
            return self._get_official_calendar_matches(days_ahead)
    
    def _get_rapidapi_matches(self, days_ahead):
        """Usar RapidAPI gratuita para obtener partidos reales"""
        fixtures = []
        today = datetime.now().date()
        
        # Headers para RapidAPI (sin key requerida para tier gratuito)
        headers = {
            'X-RapidAPI-Key': '',  # Vacío para tier gratuito
            'X-RapidAPI-Host': 'api-football-v1.p.rapidapi.com'
        }
        
        # IDs de ligas para RapidAPI
        rapidapi_leagues = {
            'E0': 39,   # Premier League
            'SP1': 140, # La Liga
            'D1': 78,   # Bundesliga
            'I1': 135,  # Serie A
            'F1': 61    # Ligue 1
        }
        
        for league_code, league_id in rapidapi_leagues.items():
            try:
                url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures"
                params = {
                    'league': league_id,
                    'season': 2024,
                    'next': 10  # Próximos 10 partidos
                }
                
                response = requests.get(url, headers=headers, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    for fixture in data.get('response', []):
                        if fixture['fixture']['status']['short'] == 'NS':  # Not Started
                            match_date = datetime.fromisoformat(fixture['fixture']['date'].replace('Z', '+00:00'))
                            fixtures.append({
                                'HomeTeam': fixture['teams']['home']['name'],
                                'AwayTeam': fixture['teams']['away']['name'],
                                'Date': match_date.strftime('%Y-%m-%d'),
                                'Time': match_date.strftime('%H:%M'),
                                'League': league_code,
                                'Competition': self._get_competition_name(league_code),
                                'Status': 'SCHEDULED'
                            })
                    print(f"✅ Obtenidos {len(data.get('response', []))} partidos reales para {league_code}")
                
                time.sleep(2)  # Respetar límites de API gratuita
                
            except Exception as e:
                print(f"Error RapidAPI {league_code}: {e}")
                continue
        
        return fixtures
    
    def _get_official_calendar_matches(self, days_ahead):
        """Obtener partidos del calendario oficial de las ligas (web scraping)"""
        fixtures = []
        today = datetime.now().date()
        
        try:
            # Scraping del calendario oficial de Premier League
            premier_matches = self._scrape_premier_league_calendar()
            fixtures.extend(premier_matches)
            
            # Scraping del calendario oficial de La Liga
            laliga_matches = self._scrape_laliga_calendar()
            fixtures.extend(laliga_matches)
            
            print(f"✅ Obtenidos {len(fixtures)} partidos del calendario oficial")
            
        except Exception as e:
            print(f"Error scraping calendarios oficiales: {e}")
        
        return fixtures
    
    def _scrape_premier_league_calendar(self):
        """Scraping del calendario oficial de Premier League"""
        fixtures = []
        try:
            from bs4 import BeautifulSoup
            
            url = "https://www.premierleague.com/fixtures"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Buscar elementos de partidos próximos
                match_elements = soup.find_all('div', class_='matchList')
                
                for match in match_elements[:10]:  # Limitar a 10 partidos
                    try:
                        home_team = match.find('span', class_='teamName').text.strip()
                        away_team = match.find_all('span', class_='teamName')[1].text.strip()
                        date_elem = match.find('time')
                        
                        if date_elem:
                            date_str = date_elem.get('datetime')
                            if date_str:
                                match_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                                fixtures.append({
                                    'HomeTeam': home_team,
                                    'AwayTeam': away_team,
                                    'Date': match_date.strftime('%Y-%m-%d'),
                                    'Time': match_date.strftime('%H:%M'),
                                    'League': 'E0',
                                    'Competition': 'Premier League',
                                    'Status': 'SCHEDULED'
                                })
                    except Exception as e:
                        continue
                        
        except Exception as e:
            print(f"Error scraping Premier League: {e}")
        
        return fixtures
    
    def _scrape_laliga_calendar(self):
        """Scraping del calendario oficial de La Liga"""
        fixtures = []
        try:
            from bs4 import BeautifulSoup
            
            url = "https://www.laliga.com/en-GB/fixture"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Buscar elementos de partidos próximos
                match_elements = soup.find_all('div', class_='match-item')
                
                for match in match_elements[:10]:  # Limitar a 10 partidos
                    try:
                        teams = match.find_all('span', class_='team-name')
                        if len(teams) >= 2:
                            home_team = teams[0].text.strip()
                            away_team = teams[1].text.strip()
                            
                            date_elem = match.find('time')
                            if date_elem:
                                date_str = date_elem.get('datetime')
                                if date_str:
                                    match_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                                    fixtures.append({
                                        'HomeTeam': home_team,
                                        'AwayTeam': away_team,
                                        'Date': match_date.strftime('%Y-%m-%d'),
                                        'Time': match_date.strftime('%H:%M'),
                                        'League': 'SP1',
                                        'Competition': 'La Liga',
                                        'Status': 'SCHEDULED'
                                    })
                    except Exception as e:
                        continue
                        
        except Exception as e:
            print(f"Error scraping La Liga: {e}")
        
        return fixtures
    
    def _get_competition_name(self, league_code):
        """Obtener nombre de la competición"""
        competition_names = {
            'E0': 'Premier League',
            'SP1': 'La Liga',
            'D1': 'Bundesliga',
            'I1': 'Serie A',
            'F1': 'Ligue 1'
        }
        return competition_names.get(league_code, 'Unknown League')
    
    def get_team_stats(self, team_name):
        """Obtener estadísticas reales del equipo desde API"""
        try:
            # Implementar obtención de estadísticas reales
            # Por ahora retornar None para forzar uso de datos reales
            return None
        except Exception as e:
            print(f"Error obteniendo estadísticas de {team_name}: {e}")
            return None
    
    def get_head_to_head(self, team1, team2):
        """Obtener historial de enfrentamientos desde API"""
        try:
            # Implementar obtención de H2H reales
            # Por ahora retornar None para forzar uso de datos reales
            return None
        except Exception as e:
            print(f"Error obteniendo H2H {team1} vs {team2}: {e}")
            return None