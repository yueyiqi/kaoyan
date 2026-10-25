"""Compatibility entry point for behavioral HTTPS acceptance; browser tests are separate."""
from verify_admin_live import main

if __name__ == '__main__':
    raise SystemExit(main())
