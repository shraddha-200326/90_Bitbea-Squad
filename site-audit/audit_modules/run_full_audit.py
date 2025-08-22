from audit_modules.seo import check_seo
from audit_modules.security import check_security
from audit_modules.performance import check_performance

def run_full_audit(url):
    return {
        'seo': check_seo(url),
        'security': check_security(url),
        'performance': check_performance(url)
    }
