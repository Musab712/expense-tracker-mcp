from fastmcp import FastMCP
import os
from supabase import create_client, Client
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

mcp = FastMCP("ExpenseTrackerTest")

def init_db():
    """
    Note: Table creation should be done via Supabase Dashboard or SQL Editor.
    This function is kept for compatibility but won't create tables.
    
    SQL to run in Supabase SQL Editor:
    
    CREATE TABLE IF NOT EXISTS expenses_test_test (
        id BIGSERIAL PRIMARY KEY,
        date TEXT NOT NULL,
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        subcategory TEXT DEFAULT '',
        note TEXT DEFAULT '',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    -- Optional: Add indexes for better performance
    CREATE INDEX IF NOT EXISTS idx_expenses_test_date ON expenses_test(date);
    CREATE INDEX IF NOT EXISTS idx_expenses_test_category ON expenses_test(category);
    """
    try:
        # Test connection by querying the table
        result = supabase.table("expenses_test").select("id").limit(1).execute()
        print("✓ Successfully connected to Supabase")
        print(f"✓ Database accessible with {len(result.data)} test records")
    except Exception as e:
        print(f"⚠ Database connection warning: {e}")
        print("Make sure the 'expenses_test' table exists in Supabase")

# Initialize database connection at module load
init_db()

@mcp.tool()
async def add_expense(date: str, amount: float, category: str, subcategory: str = "", note: str = ""):
    '''Add a new expense entry to the database.
    
    Args:
        date: Date in YYYY-MM-DD format
        amount: Expense amount (positive number)
        category: Expense category
        subcategory: Optional subcategory
        note: Optional note or description
    '''
    try:
        # Validate date format
        datetime.strptime(date, "%Y-%m-%d")
        
        data = {
            "date": date,
            "amount": float(amount),
            "category": category,
            "subcategory": subcategory,
            "note": note
        }
        
        result = supabase.table("expenses_test").insert(data).execute()
        
        if result.data and len(result.data) > 0:
            expense_id = result.data[0]["id"]
            return {
                "status": "success",
                "id": expense_id,
                "message": "Expense added successfully",
                "data": result.data[0]
            }
        else:
            return {"status": "error", "message": "Failed to add expense"}
            
    except ValueError as e:
        return {"status": "error", "message": f"Invalid date format. Use YYYY-MM-DD: {str(e)}"}
    except Exception as e:
        return {"status": "error", "message": f"Database error: {str(e)}"}

@mcp.tool()
async def list_expenses(start_date: str, end_date: str):
    '''List expense entries within an inclusive date range.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    '''
    try:
        result = supabase.table("expenses_test")\
            .select("id, date, amount, category, subcategory, note")\
            .gte("date", start_date)\
            .lte("date", end_date)\
            .order("date", desc=True)\
            .order("id", desc=True)\
            .execute()
        
        return result.data
    except Exception as e:
        return {"status": "error", "message": f"Error listing expenses: {str(e)}"}

@mcp.tool()
async def summarize(start_date: str, end_date: str, category: str = None):
    '''Summarize expenses by category within an inclusive date range.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        category: Optional category to filter by
    '''
    try:
        # Fetch all expenses_test in the date range
        query = supabase.table("expenses_test")\
            .select("category, amount")\
            .gte("date", start_date)\
            .lte("date", end_date)
        
        if category:
            query = query.eq("category", category)
        
        result = query.execute()
        
        # Group by category and calculate totals
        summary = {}
        for expense in result.data:
            cat = expense["category"]
            amount = expense["amount"]
            
            if cat not in summary:
                summary[cat] = {"category": cat, "total_amount": 0, "count": 0}
            
            summary[cat]["total_amount"] += amount
            summary[cat]["count"] += 1
        
        # Convert to list and sort by total_amount
        summary_list = sorted(
            summary.values(),
            key=lambda x: x["total_amount"],
            reverse=True
        )
        
        return summary_list
    except Exception as e:
        return {"status": "error", "message": f"Error summarizing expenses_test: {str(e)}"}

@mcp.tool()
async def delete_expense(expense_id: int):
    '''Delete an expense entry by ID.
    
    Args:
        expense_id: The ID of the expense to delete
    '''
    try:
        result = supabase.table("expenses_test")\
            .delete()\
            .eq("id", expense_id)\
            .execute()
        
        return {
            "status": "success",
            "message": f"Expense {expense_id} deleted successfully"
        }
    except Exception as e:
        return {"status": "error", "message": f"Error deleting expense: {str(e)}"}

@mcp.tool()
async def update_expense(
    expense_id: int,
    date: str = None,
    amount: float = None,
    category: str = None,
    subcategory: str = None,
    note: str = None
):
    '''Update an existing expense entry.
    
    Args:
        expense_id: The ID of the expense to update
        date: New date (optional)
        amount: New amount (optional)
        category: New category (optional)
        subcategory: New subcategory (optional)
        note: New note (optional)
    '''
    try:
        update_data = {}
        if date is not None:
            datetime.strptime(date, "%Y-%m-%d")  # Validate format
            update_data["date"] = date
        if amount is not None:
            update_data["amount"] = float(amount)
        if category is not None:
            update_data["category"] = category
        if subcategory is not None:
            update_data["subcategory"] = subcategory
        if note is not None:
            update_data["note"] = note
        
        if not update_data:
            return {"status": "error", "message": "No fields to update"}
        
        result = supabase.table("expenses_test")\
            .update(update_data)\
            .eq("id", expense_id)\
            .execute()
        
        return {
            "status": "success",
            "message": f"Expense {expense_id} updated successfully",
            "data": result.data
        }
    except ValueError as e:
        return {"status": "error", "message": f"Invalid date format. Use YYYY-MM-DD: {str(e)}"}
    except Exception as e:
        return {"status": "error", "message": f"Error updating expense: {str(e)}"}

@mcp.resource("expense:///categories", mime_type="application/json")
def categories():
    '''Returns available expense categories as JSON.'''
    default_categories = {
        "categories": [
            "Food & Dining",
            "Transportation",
            "Shopping",
            "Entertainment",
            "Bills & Utilities",
            "Healthcare",
            "Travel",
            "Education",
            "Business",
            "Personal Care",
            "Groceries",
            "Housing",
            "Insurance",
            "Gifts & Donations",
            "Other"
        ]
    }
    return json.dumps(default_categories, indent=2)

# Start the server
if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)