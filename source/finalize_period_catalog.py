# SPDX-License-Identifier: MIT
"""Apply the approved gray/black/white palette to selected projects, then render."""
import sys
import finalize_portrait_oval as final

if __name__ == '__main__':
    final.render.DS = [d for d in final.render.DS if len(sys.argv)==1 or d['id'] in sys.argv[1:]]
    final.main()
