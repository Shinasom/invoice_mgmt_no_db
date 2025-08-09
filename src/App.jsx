import React, { useState, useCallback, useEffect } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from 'recharts';
import {
  ChevronDown,
  Search,
  PlusCircle,
  Upload,
  MoreVertical,
  FileText,
  Settings,
  LayoutDashboard,
  BarChart2,
  DollarSign,
  ArrowRight,
  Bell,
  User,
  Tag,
  Trash2,
  Edit,
  Sparkles,
  Loader,
  X,
  CheckCircle,
  AlertCircle,
  Info,
  Zap,
  Eye,
  Target,
  Menu
} from 'lucide-react';
import { useDropzone } from 'react-dropzone';

// --- MOCK DATA --- //
const mockInvoices = [
  {
    id: 'INV-001',
    vendor: 'Amazon Web Services',
    category: 'Cloud Services',
    date: '2025-07-04',
    amount: 1250.75,
    status: 'Paid',
    imageUrl:
      'https://placehold.co/600x800/EEE/31343C?text=Invoice+INV-001',
  },
  {
    id: 'INV-002',
    vendor: 'Figma',
    category: 'Software',
    date: '2025-07-03',
    amount: 180.0,
    status: 'Paid',
    imageUrl:
      'https://placehold.co/600x800/EEE/31343C?text=Invoice+INV-002',
  },
  {
    id: 'INV-003',
    vendor: 'The Coffee House',
    category: 'Food & Drink',
    date: '2025-07-03',
    amount: 25.5,
    status: 'Processing',
    imageUrl:
      'https://placehold.co/600x800/EEE/31343C?text=Invoice+INV-003',
  },
  {
    id: 'INV-004',
    vendor: 'Uber',
    category: 'Travel',
    date: '2025-07-02',
    amount: 45.3,
    status: 'Paid',
    imageUrl:
      'https://placehold.co/600x800/EEE/31343C?text=Invoice+INV-004',
  },
  {
    id: 'INV-005',
    vendor: 'Linear',
    category: 'Software',
    date: '2025-07-01',
    amount: 50.0,
    status: 'Paid',
    imageUrl:
      'https://placehold.co/600x800/EEE/31343C?text=Invoice+INV-005',
  },
  {
    id: 'INV-006',
    vendor: 'Indigo Airlines',
    category: 'Travel',
    date: '2025-06-28',
    amount: 7800.0,
    status: 'Paid',
    imageUrl:
      'https://placehold.co/600x800/EEE/31343C?text=Invoice+INV-006',
  },
  {
    id: 'INV-007',
    vendor: 'Local Office Supplies',
    category: 'Office Supplies',
    date: '2025-06-25',
    amount: 215.0,
    status: 'Needs Review',
    imageUrl:
      'https://placehold.co/600x800/EEE/31343C?text=Invoice+INV-007',
  },
  {
    id: 'INV-008',
    vendor: 'Zomato',
    category: 'Food & Drink',
    date: '2025-06-24',
    amount: 75.0,
    status: 'Paid',
    imageUrl:
      'https://placehold.co/600x800/EEE/31343C?text=Invoice+INV-008',
  },
];

const mockBudgets = [
  { id: 1, category: 'Software', budget: 500, spent: 230, color: 'bg-blue-500' },
  {
    id: 2,
    category: 'Cloud Services',
    budget: 1500,
    spent: 1250.75,
    color: 'bg-purple-500',
  },
  { id: 3, category: 'Travel', budget: 8500, spent: 7845.3, color: 'bg-green-500' },
  {
    id: 4,
    category: 'Food & Drink',
    budget: 400,
    spent: 100.5,
    color: 'bg-orange-500',
  },
  {
    id: 5,
    category: 'Office Supplies',
    budget: 300,
    spent: 215.0,
    color: 'bg-yellow-500',
  },
];

const spendingByCategory = [
  { name: 'Cloud Services', value: 1250.75 },
  { name: 'Software', value: 230.0 },
  { name: 'Travel', value: 7845.3 },
  { name: 'Food & Drink', value: 100.5 },
  { name: 'Office Supplies', value: 215.0 },
];

const spendingOverTime = [
  { date: 'Jan', spending: 4000 },
  { date: 'Feb', spending: 3000 },
  { date: 'Mar', spending: 5000 },
  { date: 'Apr', spending: 4500 },
  { date: 'May', spending: 6000 },
  { date: 'Jun', spending: 8160.5 },
  { date: 'Jul', spending: 1476.55 },
];

const PIE_COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#AF19FF'];

// --- FAKE GEMINI API CALL --- //
const fakeGeminiAPI = (prompt) => {
  console.log('Sending prompt to Gemini:', prompt);
  return new Promise((resolve) => {
    setTimeout(() => {
      if (prompt.includes('budget')) {
        resolve(`- **Travel Overspend:** You've spent ₹7,845.30 on Travel, which is 92% of your ₹8,500 budget. Consider looking for cheaper flight options or reducing non-essential trips for the rest of the month.
- **Software Under-utilized:** Your Software budget is ₹500, but you've only spent ₹230. You could re-allocate ~₹200 from this budget to categories where you overspend, like Food & Drink.
- **Cloud Services Cost:** Your AWS bill is a significant fixed cost. It might be worth exploring cost-saving plans or reserved instances to reduce this monthly expense.
- **Food & Drink:** You are well within your 'Food & Drink' budget. This is an area where you have some flexibility.`);
      } else {
        resolve(`- **High Travel Spending:** Travel accounts for the largest portion of your expenses at ₹7,845.30. The Indigo Airlines flight is the primary driver of this cost.
- **Recurring Software Costs:** You have two recurring software subscriptions this month (Figma, Linear). It's good practice to review these annually to ensure they are still providing value.
- **Anomaly Detected:** The invoice from 'Local Office Supplies' (₹215.00) is significantly higher than your usual spending in this category. You may want to review the purchase details to ensure it's a valid one-time expense.
- **Frequent Food & Drink Expenses:** While the individual amounts are small, your expenses on Food & Drink are frequent. These can add up over time, so keep an eye on this category.`);
      }
    }, 1500);
  });
};

// --- REUSABLE COMPONENTS --- //
const Card = ({ children, className = '' }) => (
  <div className={`bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 ${className}`}>
    {children}
  </div>
);

const KPI_Card = ({ title, value, icon, change, changeType }) => (
  <Card>
    <div className="flex items-center justify-between">
      <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{title}</p>
      <div className="text-gray-400 dark:text-gray-500">{icon}</div>
    </div>
    <div className="mt-2">
      <p className="text-3xl font-bold text-gray-900 dark:text-white">{value}</p>
      {change && (
        <div
          className={`text-sm mt-1 ${
            changeType === 'increase' ? 'text-red-500' : 'text-green-500'
          }`}
        >
          {change} vs last month
        </div>
      )}
    </div>
  </Card>
);

const Button = ({ children, onClick, variant = 'primary', className = '', disabled = false }) => {
  const baseClasses =
    'px-4 py-2 rounded-lg font-semibold flex items-center justify-center transition-colors';
  const variants = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 disabled:bg-blue-400',
    secondary:
      'bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-600 disabled:bg-gray-400',
    ghost:
      'bg-transparent text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700',
    danger: 'bg-red-600 text-white hover:bg-red-700 disabled:bg-red-400',
  };
  return (
    <button
      onClick={onClick}
      className={`${baseClasses} ${variants[variant]} ${className}`}
      disabled={disabled}
    >
      {children}
    </button>
  );
};

// --- MODAL COMPONENTS --- //
const UploadModal = ({ isOpen, onClose, existingInvoices }) => {
  const [files, setFiles] = useState([]);
  const [step, setStep] = useState('upload'); // 'upload', 'processing', 'duplicate', 'summary'
  const [duplicateInfo, setDuplicateInfo] = useState(null);

  const onDrop = useCallback((acceptedFiles) => {
    const newFiles = acceptedFiles.map((file) => ({
      file,
      status: 'waiting',
      progress: 0,
      id: Math.random().toString(36).substring(2, 9),
    }));
    setFiles((prevFiles) => [...prevFiles, ...newFiles]);
    setStep('processing');
  }, []);

  const processSingleFile = useCallback(
    (fileWrapper) => {
      const updateStatus = (status, progress) => {
        setFiles((prev) =>
          prev.map((f) => (f.id === fileWrapper.id ? { ...f, status, progress } : f))
        );
      };

      const potentialDuplicate = existingInvoices.find((inv) =>
        fileWrapper.file.name
          .toLowerCase()
          .includes(inv.vendor.toLowerCase().split(' ')[0])
      );

      if (potentialDuplicate) {
        setDuplicateInfo({
          newFile: fileWrapper.file,
          existingInvoice: potentialDuplicate,
        });
        updateStatus('duplicate', 60);
        setStep('duplicate');
        return;
      }

      updateStatus('uploading', 20);
      setTimeout(() => {
        updateStatus('extracting text', 40);
        setTimeout(() => {
          updateStatus('analyzing', 80);
          setTimeout(() => {
            updateStatus('complete', 100);
          }, 800);
        }, 1000);
      }, 800);
    },
    [existingInvoices]
  );

  const resumeProcessingAfterDuplicate = (fileWrapper) => {
    const updateStatus = (status, progress) => {
      setFiles((prev) =>
        prev.map((f) => (f.id === fileWrapper.id ? { ...f, status, progress } : f))
      );
    };
    updateStatus('analyzing', 80);
    setTimeout(() => {
      updateStatus('complete', 100);
    }, 800);
  };

  useEffect(() => {
    if (step === 'processing') {
      const fileToProcess = files.find(
        (f) => f.status === 'waiting' || f.status === 'waiting_final'
      );
      if (fileToProcess) {
        if (fileToProcess.status === 'waiting_final') {
          resumeProcessingAfterDuplicate(fileToProcess);
        } else {
          processSingleFile(fileToProcess);
        }
      } else if (
        files.length > 0 &&
        files.every((f) => f.status === 'complete' || f.status === 'discarded')
      ) {
        setTimeout(() => setStep('summary'), 500);
      }
    }
  }, [step, files, processSingleFile]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.jpeg', '.png'], 'application/pdf': ['.pdf'] },
  });

  const handleClose = () => {
    setFiles([]);
    setStep('upload');
    setDuplicateInfo(null);
    onClose();
  };

  const handleSaveAnyway = () => {
    const duplicateFile = files.find((f) => f.status === 'duplicate');
    if (duplicateFile) {
      setFiles((prev) =>
        prev.map((f) =>
          f.id === duplicateFile.id ? { ...f, status: 'waiting_final' } : f
        )
      );
    }
    setDuplicateInfo(null);
    setStep('processing');
  };

  const handleDiscardUpload = () => {
    const duplicateFile = files.find((f) => f.status === 'duplicate');
    if (duplicateFile) {
      setFiles((prev) =>
        prev.map((f) =>
          f.id === duplicateFile.id ? { ...f, status: 'discarded', progress: 0 } : f
        )
      );
    }
    setDuplicateInfo(null);
    setStep('processing');
  };

  const renderContent = () => {
    switch (step) {
      case 'upload':
        return (
          <div
            {...getRootProps()}
            className={`p-10 border-2 border-dashed rounded-lg text-center cursor-pointer transition-colors ${
              isDragActive
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-300 dark:border-gray-600 hover:border-blue-500'
            }`}
          >
            <input {...getInputProps()} />
            <Upload className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-2 font-semibold text-gray-900 dark:text-white">
              Drag & Drop Invoice Files Here
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              or click to browse
            </p>
            <p className="mt-4 text-xs text-gray-400">
              Supported formats: PDF, PNG, JPG. Try a filename with 'Uber' to
              test duplicate check.
            </p>
          </div>
        );
      case 'processing':
      case 'summary': {
        const visibleFiles = files.filter((f) => f.status !== 'discarded');
        return (
          <div>
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
              {step === 'processing' ? 'Processing Invoices...' : 'Upload Summary'}
            </h3>
            <div className="space-y-4">
              {visibleFiles.map((fileWrapper) => (
                <div key={fileWrapper.id}>
                  <div className="flex justify-between items-center text-sm">
                    <p className="font-medium text-gray-800 dark:text-gray-200 truncate pr-4">
                      {fileWrapper.file.name}
                    </p>
                    <div className="flex items-center">
                      <span className="text-gray-500 dark:text-gray-400 capitalize mr-2">
                        {fileWrapper.status.replace('_', ' ')}
                      </span>
                      {fileWrapper.status === 'complete' && (
                        <CheckCircle className="h-5 w-5 text-green-500" />
                      )}
                      {fileWrapper.status === 'duplicate' && (
                        <AlertCircle className="h-5 w-5 text-yellow-500" />
                      )}
                      {fileWrapper.progress > 0 && fileWrapper.progress < 100 && (
                        <Loader className="animate-spin h-5 w-5 text-blue-500" />
                      )}
                    </div>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 mt-1">
                    <div
                      className="bg-blue-600 h-1.5 rounded-full"
                      style={{ width: `${fileWrapper.progress}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      }
      case 'duplicate':
        return (
          <div>
            <h3 className="text-lg font-semibold text-yellow-500 flex items-center">
              <AlertCircle className="mr-2" /> Possible Duplicate Detected
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              This invoice seems similar to an existing one.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
              <div>
                <h4 className="font-semibold text-center mb-2">
                  Existing Invoice ({duplicateInfo?.existingInvoice?.id})
                </h4>
                {duplicateInfo?.existingInvoice?.imageUrl && (
                  <img
                    src={duplicateInfo.existingInvoice.imageUrl}
                    alt="Existing invoice"
                    className="rounded-lg border dark:border-gray-600"
                  />
                )}
              </div>
              <div>
                <h4 className="font-semibold text-center mb-2">New Upload</h4>
                {duplicateInfo?.newFile && (
                  <img
                    src={URL.createObjectURL(duplicateInfo.newFile)}
                    alt="New invoice"
                    className="rounded-lg border dark:border-gray-600"
                  />
                )}
              </div>
            </div>
            <div className="flex justify-end space-x-3 mt-6">
              <Button variant="danger" onClick={handleDiscardUpload}>
                Discard Upload
              </Button>
              <Button variant="primary" onClick={handleSaveAnyway}>
                Save Anyway
              </Button>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-2xl p-6 relative max-h-[90vh] overflow-y-auto">
        <button
          onClick={handleClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
        >
          <X className="h-6 w-6" />
        </button>
        {renderContent()}
        {step === 'summary' && (
          <div className="flex justify-end space-x-3 mt-6">
            <Button
              variant="secondary"
              onClick={() => {
                setFiles([]);
                setStep('upload');
              }}
            >
              Upload More
            </Button>
            <Button variant="primary" onClick={handleClose}>
              Done
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

const AboutModal = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  const Feature = ({ icon, title, children }) => (
    <div className="flex">
      <div className="flex-shrink-0 mr-4">
        <div className="bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400 rounded-lg h-10 w-10 flex items-center justify-center">
          {icon}
        </div>
      </div>
      <div>
        <h4 className="text-lg font-semibold text-gray-900 dark:text-white">{title}</h4>
        <p className="mt-1 text-gray-600 dark:text-gray-300">{children}</p>
      </div>
    </div>
  );

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-2xl p-8 relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
        >
          <X className="h-6 w-6" />
        </button>
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Welcome to InvoiceAI
          </h2>
          <p className="mt-2 text-lg text-gray-600 dark:text-gray-300">
            Turn your chaotic pile of receipts and invoices into clear,
            actionable insights.
          </p>
        </div>
        <div className="mt-8 space-y-6">
          <Feature icon={<Zap size={20} />} title="Effortless Data Extraction">
            Stop manual data entry. Upload any invoice, and our AI instantly
            extracts and categorizes the key details for you.
          </Feature>
          <Feature icon={<Eye size={20} />} title="Clear Financial Visibility">
            No more guessing. Our interactive dashboard gives you an at-a-glance
            overview of your spending so you always know where your money is
            going.
          </Feature>
          <Feature icon={<Target size={20} />} title="Intelligent Insights & Security">
            Go beyond simple tracking. Our AI analyzes your habits, provides
            cost-saving tips, and flags potential duplicate invoices to protect
            your finances.
          </Feature>
        </div>
        <div className="mt-8 text-center text-xs text-gray-400 dark:text-gray-500">
          <p>
            This application demonstrates a full-stack portfolio project using
            modern AI and web technologies.
          </p>
        </div>
      </div>
    </div>
  );
};

// --- PAGE COMPONENTS --- //
const Dashboard = ({ onUploadClick }) => (
  <div className="space-y-6">
    <div className="flex justify-between items-center">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
      <div className="flex items-center space-x-2">
        <Button variant="secondary">Export Report</Button>
        <Button onClick={onUploadClick}>
          <PlusCircle className="mr-2 h-5 w-5" /> Upload Invoice
        </Button>
      </div>
    </div>
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <KPI_Card
        title="Total Spending (Month)"
        value="₹9,637.05"
        icon={<DollarSign />}
        change="+15.2%"
        changeType="increase"
      />
      <KPI_Card title="Invoices to Review" value="1" icon={<FileText />} />
      <KPI_Card title="Avg. Spend / Invoice" value="₹1,204.63" icon={<BarChart2 />} />
      <KPI_Card title="Highest Category" value="Travel" icon={<Tag />} />
    </div>
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <Card className="lg:col-span-2">
        <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
          Spending Over Time
        </h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={spendingOverTime}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(128, 128, 128, 0.2)" />
            <XAxis dataKey="date" stroke="#9CA3AF" />
            <YAxis stroke="#9CA3AF" />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1F2937',
                border: 'none',
                borderRadius: '0.5rem',
              }}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="spending"
              stroke="#3B82F6"
              strokeWidth={2}
              activeDot={{ r: 8 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </Card>
      <Card>
        <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
          Spending by Category
        </h2>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={spendingByCategory}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              outerRadius={100}
              fill="#8884d8"
              label
            >
              {spendingByCategory.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: '#1F2937',
                border: 'none',
                borderRadius: '0.5rem',
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </Card>
    </div>
    <Card>
      <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
        Recent Invoices
      </h2>
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead className="text-xs text-gray-500 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400">
            <tr>
              <th className="px-6 py-3">Invoice ID</th>
              <th className="px-6 py-3">Vendor</th>
              <th className="px-6 py-3">Category</th>
              <th className="px-6 py-3">Date</th>
              <th className="px-6 py-3">Amount</th>
              <th className="px-6 py-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {mockInvoices.slice(0, 5).map((invoice) => (
              <tr
                key={invoice.id}
                className="bg-white dark:bg-gray-800 border-b dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600"
              >
                <td className="px-6 py-4 font-medium text-gray-900 dark:text-white">
                  {invoice.id}
                </td>
                <td className="px-6 py-4">{invoice.vendor}</td>
                <td className="px-6 py-4">{invoice.category}</td>
                <td className="px-6 py-4">{invoice.date}</td>
                <td className="px-6 py-4">₹{invoice.amount.toFixed(2)}</td>
                <td className="px-6 py-4">
                  <span
                    className={`px-2 py-1 rounded-full text-xs font-medium ${
                      invoice.status === 'Paid'
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
                        : invoice.status === 'Processing'
                        ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
                        : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
                    }`}
                  >
                    {invoice.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  </div>
);

// Add a compact mobile card for invoices
const InvoiceCard = ({ invoice }) => (
  <div className="md:hidden bg-white dark:bg-gray-800 rounded-lg shadow border dark:border-gray-700 p-4 flex items-start justify-between">
    <div className="pr-3 min-w-0">
      <p className="text-xs text-gray-500 dark:text-gray-400">{invoice.id}</p>
      <p className="mt-1 font-semibold text-gray-900 dark:text-white truncate">{invoice.vendor}</p>
      <p className="text-sm text-gray-600 dark:text-gray-300 truncate">{invoice.category}</p>
      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{invoice.date}</p>
    </div>
    <div className="text-right flex-shrink-0">
      <p className="font-bold text-gray-900 dark:text-white">₹{invoice.amount.toFixed(2)}</p>
      <span className={`inline-block mt-2 px-2 py-1 rounded-full text-xs font-medium ${
        invoice.status === 'Paid'
          ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
          : invoice.status === 'Processing'
          ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
          : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
      }`}>{invoice.status}</span>
    </div>
  </div>
);

const InvoicesPage = ({ onUploadClick }) => (
  <div className="space-y-6">
    <div className="flex justify-between items-center">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Invoices</h1>
      <Button onClick={onUploadClick}>
        <PlusCircle className="mr-2 h-5 w-5" /> Upload Invoice
      </Button>
    </div>
    <Card>
      <div className="flex flex-col md:flex-row justify-between items-center space-y-2 md:space-y-0 md:space-x-4 mb-4">
        <div className="relative w-full md:w-1/3">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search by vendor or ID..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-700 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="secondary">
            Filter by Category <ChevronDown className="ml-2 h-4 w-4" />
          </Button>
          <Button variant="secondary">
            Filter by Date <ChevronDown className="ml-2 h-4 w-4" />
          </Button>
          <Button variant="secondary">
            Bulk Actions <ChevronDown className="ml-2 h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Mobile: card list */}
      <div className="space-y-3 md:hidden">
        {mockInvoices.map((invoice) => (
          <InvoiceCard key={invoice.id} invoice={invoice} />
        ))}
      </div>

      {/* Desktop/tablet: table */}
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full text-left">
          <thead className="text-xs text-gray-500 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400">
            <tr>
              <th className="p-4">
                <input
                  type="checkbox"
                  className="form-checkbox h-4 w-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                />
              </th>
              <th className="px-6 py-3">Invoice ID</th>
              <th className="px-6 py-3">Vendor</th>
              <th className="px-6 py-3">Category</th>
              <th className="px-6 py-3">Date</th>
              <th className="px-6 py-3">Amount</th>
              <th className="px-6 py-3">Status</th>
              <th className="px-6 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {mockInvoices.map((invoice) => (
              <tr
                key={invoice.id}
                className="bg-white dark:bg-gray-800 border-b dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600"
              >
                <td className="p-4">
                  <input
                    type="checkbox"
                    className="form-checkbox h-4 w-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                  />
                </td>
                <td className="px-6 py-4 font-medium text-gray-900 dark:text-white">
                  {invoice.id}
                </td>
                <td className="px-6 py-4">{invoice.vendor}</td>
                <td className="px-6 py-4">{invoice.category}</td>
                <td className="px-6 py-4">{invoice.date}</td>
                <td className="px-6 py-4">₹{invoice.amount.toFixed(2)}</td>
                <td className="px-6 py-4">
                  <span
                    className={`px-2 py-1 rounded-full text-xs font-medium ${
                      invoice.status === 'Paid'
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
                        : invoice.status === 'Processing'
                        ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
                        : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
                    }`}
                  >
                    {invoice.status}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <Button variant="ghost" className="p-2 h-8 w-8">
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  </div>
);

const AnalyticsPage = () => {
  const [insights, setInsights] = useState('');
  const [isLoadingInsights, setIsLoadingInsights] = useState(false);

  const handleGenerateInsights = async () => {
    setIsLoadingInsights(true);
    const prompt = `Analyze the following invoice data and provide 3-4 bullet-point insights. Focus on key spending trends, anomalies, and potential cost-saving opportunities.\n\nData:\n${JSON.stringify(
      mockInvoices,
      null,
      2
    )}`;
    const result = await fakeGeminiAPI(prompt);
    setInsights(result);
    setIsLoadingInsights(false);
  };

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Analytics</h1>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
            Spending by Vendor
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={spendingByCategory}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(128, 128, 128, 0.2)" />
              <XAxis type="number" stroke="#9CA3AF" />
              <YAxis type="category" dataKey="name" width={100} stroke="#9CA3AF" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: 'none',
                  borderRadius: '0.5rem',
                }}
              />
              <Bar dataKey="value" fill="#3B82F6" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
        <Card>
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
            Monthly Spending Trend
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={spendingOverTime}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(128, 128, 128, 0.2)" />
              <XAxis dataKey="date" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: 'none',
                  borderRadius: '0.5rem',
                }}
              />
              <Legend />
              <Line type="monotone" dataKey="spending" stroke="#8884d8" activeDot={{ r: 8 }} />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </div>
      <Card>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">✨ AI Insights</h2>
          <Button onClick={handleGenerateInsights} disabled={isLoadingInsights}>
            {isLoadingInsights ? (
              <>
                <Loader className="animate-spin mr-2 h-5 w-5" /> Generating...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-5 w-5" /> Generate Fresh Insights
              </>
            )}
          </Button>
        </div>
        <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg min-h-[150px]">
          {isLoadingInsights ? (
            <div className="flex justify-center items-center h-full">
              <Loader className="animate-spin h-8 w-8 text-blue-500" />
            </div>
          ) : (
            <div className="text-blue-800 dark:text-blue-300 whitespace-pre-wrap">
              {insights ||
                'Click the button to generate AI-powered insights on your spending.'}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};

const BudgetsPage = () => {
  const [budgetTips, setBudgetTips] = useState('');
  const [isLoadingTips, setIsLoadingTips] = useState(false);

  const handleGenerateBudgetTips = async () => {
    setIsLoadingTips(true);
    const prompt = `Analyze my spending (JSON: ${JSON.stringify(
      mockInvoices
    )}) against my budgets (JSON: ${JSON.stringify(
      mockBudgets
    )}) and provide actionable recommendations to optimize my budget.`;
    const result = await fakeGeminiAPI(prompt);
    setBudgetTips(result);
    setIsLoadingTips(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Budgets</h1>
        <Button>
          <PlusCircle className="mr-2 h-5 w-5" /> New Budget
        </Button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {mockBudgets.map((budget) => {
          const percentage = (budget.spent / budget.budget) * 100;
          return (
            <Card key={budget.id}>
              <div className="flex justify-between items-center">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {budget.category}
                </h2>
                <span className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  ₹{budget.spent.toFixed(2)} / ₹{budget.budget.toFixed(2)}
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5 my-3">
                <div
                  className={`${budget.color} h-2.5 rounded-full`
                  }
                  style={{ width: `${Math.min(percentage, 100)}%` }}
                ></div>
              </div>
              <div className="flex justify-between text-sm text-gray-500 dark:text-gray-400">
                <span>{percentage.toFixed(0)}% Used</span>
                <span>₹{(budget.budget - budget.spent).toFixed(2)} Remaining</span>
              </div>
            </Card>
          );
        })}
      </div>
      <Card>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            ✨ AI Budgeting Advisor
          </h2>
          <Button onClick={handleGenerateBudgetTips} disabled={isLoadingTips}>
            {isLoadingTips ? (
              <>
                <Loader className="animate-spin mr-2 h-5 w-5" /> Analyzing...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-5 w-5" /> Get AI Budgeting Tips
              </>
            )}
          </Button>
        </div>
        <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg min-h-[150px]">
          {isLoadingTips ? (
            <div className="flex justify-center items-center h-full">
              <Loader className="animate-spin h-8 w-8 text-purple-500" />
            </div>
          ) : (
            <div className="text-purple-800 dark:text-purple-300 whitespace-pre-wrap">
              {budgetTips ||
                'Click the button to get personalized tips on how to optimize your budgets.'}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};

const SettingsPage = () => (
  <div className="space-y-8">
    <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Settings</h1>
    <Card>
      <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Profile</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Full Name
          </label>
          <input
            type="text"
            defaultValue="John Doe"
            className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm py-2 px-3 bg-white dark:bg-gray-700 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Email Address
          </label>
          <input
            type="email"
            defaultValue="john.doe@example.com"
            className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm py-2 px-3 bg-white dark:bg-gray-700 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          />
        </div>
      </div>
      <div className="mt-6">
        <Button>Save Changes</Button>
      </div>
    </Card>

    <Card>
      <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
        Category Management
      </h2>
      <div className="space-y-3">
        {mockBudgets.map((b) => (
          <div
            key={b.id}
            className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
          >
            <div className="flex items-center">
              <span className={`h-3 w-3 rounded-full mr-3 ${b.color}`}></span>
              <span className="text-gray-800 dark:text-gray-200">{b.category}</span>
            </div>
            <div className="flex items-center space-x-2">
              <Button variant="ghost" className="p-2 h-8 w-8">
                <Edit className="h-4 w-4" />
              </Button>
              <Button variant="ghost" className="p-2 h-8 w-8 text-red-500">
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        ))}
      </div>
      <div className="mt-6">
        <Button variant="secondary">
          <PlusCircle className="mr-2 h-5 w-5" /> Add New Category
        </Button>
      </div>
    </Card>

    <Card>
      <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
        Notifications
      </h2>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <p className="text-gray-800 dark:text-gray-200">Email me for budget alerts</p>
          <label className="relative inline-flex items-center cursor-pointer">
            <input type="checkbox" value="" className="sr-only peer" defaultChecked />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
          </label>
        </div>
        <div className="flex items-center justify-between">
          <p className="text-gray-800 dark:text-gray-200">
            Push notifications for new invoices
          </p>
          <label className="relative inline-flex items-center cursor-pointer">
            <input type="checkbox" value="" className="sr-only peer" />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
          </label>
        </div>
      </div>
    </Card>
  </div>
);

// --- MAIN APP COMPONENT --- //
export default function App() {
  const [currentPage, setCurrentPage] = useState('Dashboard');
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isAboutModalOpen, setIsAboutModalOpen] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  useEffect(() => {
    // Ensure tailwind config object exists before script loads
    if (!window.tailwind) {
      window.tailwind = {
        config: {
          // any specific configs can go here
        },
      };
    }

    const scriptId = 'tailwind-cdn-script';
    if (document.getElementById(scriptId)) return;
    const script = document.createElement('script');
    script.id = scriptId;
    script.src = 'https://cdn.tailwindcss.com';
    document.head.appendChild(script);
  }, []);

  // Close sidebar on Escape
  useEffect(() => {
    const onKeyDown = (e) => {
      if (e.key === 'Escape') setIsSidebarOpen(false);
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  const NavItem = ({ pageName, icon }) => {
    const isActive = currentPage === pageName;
    return (
      <button
        onClick={() => setCurrentPage(pageName)}
        className={`flex items-center w-full px-4 py-2.5 text-sm font-medium rounded-lg transition-colors ${
          isActive
            ? 'bg-blue-600 text-white'
            : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
        }`}
      >
        {icon}
        <span className="ml-3">{pageName}</span>
      </button>
    );
  };

  const renderPage = () => {
    const pageProps = { onUploadClick: () => setIsUploadModalOpen(true) };
    switch (currentPage) {
      case 'Dashboard':
        return <Dashboard {...pageProps} />;
      case 'Invoices':
        return <InvoicesPage {...pageProps} />;
      case 'Analytics':
        return <AnalyticsPage />;
      case 'Budgets':
        return <BudgetsPage />;
      case 'Settings':
        return <SettingsPage />;
      default:
        return <Dashboard {...pageProps} />;
    }
  };

  return (
    <div className="flex h-screen bg-gray-100 dark:bg-gray-900 text-gray-800 dark:text-gray-200">
      {isSidebarOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-30 md:hidden"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-64 transform transition-transform duration-200 bg-white dark:bg-gray-800 border-r dark:border-gray-700 flex flex-col md:static md:inset-auto md:translate-x-0 ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="h-16 flex items-center justify-center px-4 border-b dark:border-gray-700 relative">
          <FileText className="h-8 w-8 text-blue-600" />
          <h1 className="ml-2 text-xl font-bold text-gray-900 dark:text-white">InvoiceAI</h1>
          <button
            className="md:hidden absolute right-3 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
            onClick={() => setIsSidebarOpen(false)}
            aria-label="Close sidebar"
          >
            <X className="h-6 w-6" />
          </button>
        </div>
        <nav className="flex-1 p-4 space-y-2">
          <NavItem pageName="Dashboard" icon={<LayoutDashboard className="h-5 w-5" />} />
          <NavItem pageName="Invoices" icon={<FileText className="h-5 w-5" />} />
          <NavItem pageName="Analytics" icon={<BarChart2 className="h-5 w-5" />} />
          <NavItem pageName="Budgets" icon={<DollarSign className="h-5 w-5" />} />
          <NavItem pageName="Settings" icon={<Settings className="h-5 w-5" />} />
        </nav>
        <div className="p-4 border-t dark:border-gray-700">
          <Card className="!p-4 mb-2">
            <h3 className="font-semibold text-sm text-gray-900 dark:text-white">Upgrade to Pro</h3>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Get unlimited uploads, AI insights, and more.</p>
            <Button className="w-full mt-3 !py-1.5 text-sm">
              Upgrade <ArrowRight className="ml-1 h-4 w-4" />
            </Button>
          </Card>
          <button
            onClick={() => setIsAboutModalOpen(true)}
            className="w-full text-xs text-gray-500 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 flex items-center justify-center space-x-1"
          >
            <Info className="h-3 w-3" />
            <span>About InvoiceAI</span>
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto">
        <header className="h-16 bg-white dark:bg-gray-800 border-b dark:border-gray-700 flex items-center justify-between px-6">
          <div className="md:hidden">
            <Button variant="ghost" onClick={() => setIsSidebarOpen(true)} aria-label="Open sidebar">
              <Menu className="h-6 w-6" />
            </Button>
          </div>
          <div className="flex items-center space-x-4">
            <Button variant="ghost" className="relative">
              <Bell className="h-6 w-6" />
              <span className="absolute top-0 right-0 h-2 w-2 bg-red-500 rounded-full"></span>
            </Button>
            <div className="flex items-center">
              <img className="h-9 w-9 rounded-full" src="https://placehold.co/100x100/E2E8F0/4A5568?text=JD" alt="User" />
              <div className="ml-3">
                <p className="text-sm font-semibold text-gray-900 dark:text-white">John Doe</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">john.doe@example.com</p>
              </div>
            </div>
          </div>
        </header>
        <div className="p-6">{renderPage()}</div>
      </main>

      <UploadModal 
        isOpen={isUploadModalOpen} 
        onClose={() => setIsUploadModalOpen(false)} 
        existingInvoices={mockInvoices}
      />
      <AboutModal isOpen={isAboutModalOpen} onClose={() => setIsAboutModalOpen(false)} />
    </div>
  );
}
