"""Template rendering engine"""
import re
from typing import Dict, Any


def render_template(template: str, variables: Dict[str, Any]) -> str:
    """
    Render template with variables using {{variable}} syntax
    
    Args:
        template: Template string with {{variable}} placeholders
        variables: Dictionary of variables to substitute
        
    Returns:
        Rendered template string
    """
    def replace_var(match):
        var_name = match.group(1).strip()
        return str(variables.get(var_name, f"{{{{{var_name}}}}}"))
    
    pattern = r'\{\{([^}]+)\}\}'
    return re.sub(pattern, replace_var, template)

