from datetime import date, datetime
import locale

# Configurar locale para português
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil.1252')
    except locale.Error:
        pass  # Fallback para o locale padrão

def calculate_days_difference(target_date, reference_date=None):
    """
    Calcula a diferença em dias entre duas datas.
    
    Args:
        target_date: Data alvo
        reference_date: Data de referência (padrão: hoje)
    
    Returns:
        int: Diferença em dias (positivo = futuro, negativo = passado)
    """
    if reference_date is None:
        reference_date = date.today()
    
    if isinstance(target_date, datetime):
        target_date = target_date.date()
    if isinstance(reference_date, datetime):
        reference_date = reference_date.date()
    
    return (target_date - reference_date).days

def get_delivery_status_text(delivery_date):
    """
    Retorna o texto de status da entrega baseado na data.
    
    Args:
        delivery_date: Data de entrega
    
    Returns:
        dict: {'text': str, 'class': str}
    """
    days_left = calculate_days_difference(delivery_date)
    
    if days_left < 0:
        return {
            'text': f'{-days_left} dias atrasado',
            'class': 'text-danger'
        }
    elif days_left == 0:
        return {
            'text': 'Entrega hoje',
            'class': 'text-warning'
        }
    elif days_left <= 3:
        return {
            'text': f'{days_left} dias restantes',
            'class': 'text-warning'
        }
    else:
        return {
            'text': f'{days_left} dias restantes',
            'class': 'text-muted'
        }

def get_elapsed_days_text(start_date):
    """
    Retorna o texto de dias decorridos desde uma data.
    
    Args:
        start_date: Data de início
    
    Returns:
        str: Texto formatado dos dias decorridos
    """
    elapsed_days = calculate_days_difference(date.today(), start_date)
    
    if elapsed_days == 1:
        return "1 dia"
    else:
        return f"{elapsed_days} dias"

def get_weekday_name_pt(date_obj):
    """
    Retorna o nome do dia da semana em português.
    
    Args:
        date_obj: Objeto date ou datetime
    
    Returns:
        str: Nome do dia da semana em português
    """
    weekdays_pt = {
        'Monday': 'Segunda-feira',
        'Tuesday': 'Terça-feira', 
        'Wednesday': 'Quarta-feira',
        'Thursday': 'Quinta-feira',
        'Friday': 'Sexta-feira',
        'Saturday': 'Sábado',
        'Sunday': 'Domingo'
    }
    
    if isinstance(date_obj, datetime):
        date_obj = date_obj.date()
    
    english_weekday = date_obj.strftime('%A')
    return weekdays_pt.get(english_weekday, english_weekday)

def is_delivery_urgent(delivery_date, threshold_days=3):
    """
    Verifica se uma entrega é urgente (próxima ao prazo).
    
    Args:
        delivery_date: Data de entrega
        threshold_days: Número de dias para considerar urgente
    
    Returns:
        bool: True se for urgente
    """
    days_left = calculate_days_difference(delivery_date)
    return days_left <= threshold_days and days_left >= 0

def format_date_pt(date_obj, format_type='full'):
    """
    Formata uma data em português.
    
    Args:
        date_obj: Objeto date ou datetime
        format_type: Tipo de formatação ('full', 'short', 'weekday')
    
    Returns:
        str: Data formatada
    """
    if isinstance(date_obj, datetime):
        date_obj = date_obj.date()
    
    if format_type == 'full':
        return date_obj.strftime('%d/%m/%Y')
    elif format_type == 'short':
        return date_obj.strftime('%d/%m')
    elif format_type == 'weekday':
        return get_weekday_name_pt(date_obj)
    else:
        return date_obj.strftime('%d/%m/%Y')



def format_bytes(size):
    """
    Formata um número de bytes para uma string legível.
    """
    # 2**10 = 1024
    power = 2**10
    n = 0
    byte_labels = {0 : 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {byte_labels[n]}"


